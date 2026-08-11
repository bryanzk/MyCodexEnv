#!/usr/bin/env python3
"""Detect drift between repository state and the public DHF documentation surfaces.

This is a read-only reporter. It never edits files. Callers decide what to fix.

Four drift classes are checked, matching the public-site sync contract:

  status      the `data-dhf-status` marker must be identical across every public
              HTML page and must match the literal that test_runner.py asserts
  registry    every public HTML page must be registered in surfaces.json,
              repo-index.md, and the Visual Guides list in LIFECYCLE_SKILL_ROUTING.md
  bilingual   each EN/CN page pair should have comparable structure; a large
              asymmetry usually means one language got an update the other missed
  capability  commits that touch governed runtime surfaces since the current
              status date, whose subjects are not reflected in any public page

Exit code is 0 when there is no drift, 1 when drift exists, 2 on usage error.
Use --json for machine-readable output.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Pages that are internal implementation notes rather than public nav surfaces.
NON_PUBLIC_HTML: set[str] = set()

# Governed source trees whose changes usually imply a public-doc update.
GOVERNED_PATHS = ("codex/", "scripts/", "claude/codex-hooks/")

# Words too generic to prove that a commit's capability reached the public pages.
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "only", "when",
    "then", "than", "have", "has", "add", "adds", "added", "fix", "fixes",
    "fixed", "feat", "chore", "docs", "test", "tests", "refactor", "update",
    "updates", "updated", "make", "makes", "use", "uses", "not", "now", "all",
    "new", "old", "run", "runs", "keep", "keeps", "before", "after", "without",
}


def sh(args: list[str], cwd: Path) -> str:
    out = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ""


def public_html(docs: Path) -> list[Path]:
    return sorted(p for p in docs.glob("*.html") if p.name not in NON_PUBLIC_HTML)


def check_status(root: Path, docs: Path) -> tuple[list[dict], str | None]:
    """All public pages must carry one identical status marker, matching the test."""
    findings: list[dict] = []
    markers: dict[str, str] = {}
    for page in public_html(docs):
        m = re.search(r'data-dhf-status="([^"]+)"', page.read_text(encoding="utf-8"))
        markers[page.name] = m.group(1) if m else "MISSING"

    if not markers:
        return findings, None

    counts = Counter(markers.values())
    consensus = counts.most_common(1)[0][0]
    for name, value in sorted(markers.items()):
        if value != consensus:
            findings.append({
                "class": "status",
                "severity": "high",
                "detail": f"{name} has status marker {value}, expected {consensus}",
                "fix": f"set data-dhf-status=\"{consensus}\" in docs/{name}",
            })

    runner = root / "test_runner.py"
    if runner.is_file():
        expected = re.search(r"data-dhf-status=\\\"([0-9-]+)\\\"", runner.read_text(encoding="utf-8"))
        if expected and expected.group(1) != consensus:
            findings.append({
                "class": "status",
                "severity": "high",
                "detail": (
                    f"test_runner.py asserts status {expected.group(1)} but pages carry {consensus}"
                ),
                "fix": "update the data-dhf-status literal in test_runner.py to match the pages",
            })
    return findings, consensus


def check_registry(root: Path, docs: Path) -> list[dict]:
    """Public pages must be registered, and the surface check must pass.

    surfaces.json and repo-index.md are enforced inventories: check_surfaces.py
    fails when they disagree, so a gap there is mechanically fixable. The Visual
    Guides list in LIFECYCLE_SKILL_ROUTING.md is a curated reading path, not an
    exhaustive index, so a gap there is advisory only.
    """
    findings: list[dict] = []
    inventories = {
        "surfaces.json": ("medium", docs / "surfaces.json"),
        "repo-index.md": ("medium", docs / "repo-index.md"),
        "LIFECYCLE_SKILL_ROUTING.md": ("low", docs / "LIFECYCLE_SKILL_ROUTING.md"),
    }
    for page in public_html(docs):
        for label, (severity, path) in inventories.items():
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            if page.name not in text:
                findings.append({
                    "class": "registry",
                    "severity": severity,
                    "detail": f"docs/{page.name} is not listed in docs/{label}",
                    "fix": f"add a docs/{page.name} entry to docs/{label}",
                })

    checker = root / "scripts" / "check_surfaces.py"
    if checker.is_file():
        proc = subprocess.run(
            [sys.executable, str(checker), "--repo-root", str(root),
             "--check-public-nav", "--json"],
            capture_output=True, text=True,
        )
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            payload = {}
        for err in payload.get("errors", []):
            findings.append({
                "class": "registry",
                "severity": "high",
                "detail": f"check_surfaces: {err}",
                "fix": "reconcile docs/surfaces.json with docs/repo-index.md",
            })
    return findings


def page_shape(text: str) -> dict:
    # Mermaid blocks appear as <pre class="mermaid"> on some pages and
    # <div class="mermaid"> on others, so anchor on the flowchart keyword
    # and read to the closing tag of whichever container was used.
    mermaid = "\n".join(re.findall(r"(flowchart\s+\w+.*?)</(?:pre|div)>", text, re.S))
    return {
        "sections": len(re.findall(r"<section\b", text)),
        "cards": len(re.findall(r'class="(?:card|link-card)"', text)),
        "edges": mermaid.count("-->"),
        "branches": len(re.findall(r'--\s*"', mermaid)),
    }


def check_bilingual(docs: Path) -> list[dict]:
    """EN/CN counterparts should carry comparable structure.

    Some pairs are legitimately asymmetric because one language got a fuller
    treatment on purpose, so this is reported for a human to judge rather than
    auto-corrected. Only a gap wide enough to suggest a missed update is worth
    surfacing; small differences are normal editorial variance.
    """
    findings: list[dict] = []
    for en in public_html(docs):
        if "-en.html" not in en.name:
            continue
        cn = docs / en.name.replace("-en.html", "-cn.html")
        if not cn.is_file():
            continue
        a, b = page_shape(en.read_text(encoding="utf-8")), page_shape(cn.read_text(encoding="utf-8"))
        for key in ("sections", "cards", "branches"):
            hi, lo = max(a[key], b[key]), min(a[key], b[key])
            if hi and (hi - lo) >= max(2, hi // 3):
                findings.append({
                    "class": "bilingual",
                    "severity": "low",
                    "detail": f"{en.name} has {a[key]} {key}, {cn.name} has {b[key]}",
                    "fix": (
                        f"review docs/{en.name} against docs/{cn.name}; mirror only if the "
                        f"gap is a missed update rather than a deliberate difference"
                    ),
                })
    return findings


def check_diagram_coverage(docs: Path) -> list[dict]:
    """A governance diagram is only honest if it still draws refusal and failure edges."""
    findings: list[dict] = []
    required = {
        "refusal edge": (r"Block|阻断", "a path showing what happens when the guard refuses"),
        "verification back-edge": (r"fail[^\n]*-->|失败[^\n]*-->", "a verification-failure return edge"),
        "lane gate": (r"Lane|lane", "the local / demo / production lane decision"),
    }
    pages = [p for p in public_html(docs) if "governance-decision-flow" in p.name]
    if not pages:
        findings.append({
            "class": "diagram",
            "severity": "high",
            "detail": "no governance decision flow page found",
            "fix": "restore docs/dhf-governance-decision-flow-{en,cn}.html",
        })
        return findings
    for page in pages:
        mermaid = "\n".join(
            re.findall(r"(flowchart\s+\w+.*?)</(?:pre|div)>", page.read_text(encoding="utf-8"), re.S)
        )
        for label, (pattern, why) in required.items():
            if not re.search(pattern, mermaid):
                findings.append({
                    "class": "diagram",
                    "severity": "high",
                    "detail": f"docs/{page.name} no longer draws the {label}",
                    "fix": f"restore {why}",
                })
    return findings


def check_capability(root: Path, docs: Path, lookback_days: int) -> list[dict]:
    """Recent governed-source commits should be visible somewhere on the public pages.

    The window is a rolling lookback rather than the status date, because the
    status date moves whenever the pages are refreshed. Anchoring on it would
    make this check blind itself the moment anything else got fixed.
    """
    findings: list[dict] = []
    log = sh(["git", "log", f"--since={lookback_days} days ago",
              "--format=%h%x00%s", "--name-only"], root)
    if not log:
        return findings

    corpus = " ".join(p.read_text(encoding="utf-8") for p in public_html(docs)).lower()
    blocks = [b for b in log.split("\n\n") if b.strip()]
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines or "\x00" not in lines[0]:
            continue
        sha, subject = lines[0].split("\x00", 1)
        files = lines[1:]
        if not any(f.startswith(GOVERNED_PATHS) for f in files):
            continue
        terms = {
            w for w in re.findall(r"[a-z_]{4,}", subject.lower())
            if w not in STOPWORDS
        }
        if terms and not any(t.replace("_", " ") in corpus or t in corpus for t in terms):
            findings.append({
                "class": "capability",
                "severity": "low",
                "detail": (
                    f"{sha} \"{subject}\" changed governed source but none of its terms "
                    f"({', '.join(sorted(terms))}) appear on any public page"
                ),
                "fix": "decide whether this capability belongs on the landing or status page",
            })
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", default=".", help="repository root (default: cwd)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--lookback-days", type=int, default=14,
                    help="how far back to scan governed-source commits (default: 14)")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    docs = root / "docs"
    if not docs.is_dir():
        print(f"no docs/ directory under {root}", file=sys.stderr)
        return 2

    status_findings, consensus = check_status(root, docs)
    findings = (
        status_findings
        + check_registry(root, docs)
        + check_bilingual(docs)
        + check_diagram_coverage(docs)
        + check_capability(root, docs, args.lookback_days)
    )
    rank = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: (rank.get(f["severity"], 3), f["class"], f["detail"]))

    if args.json:
        print(json.dumps({
            "ok": not findings,
            "status_date": consensus,
            "count": len(findings),
            "by_class": dict(Counter(f["class"] for f in findings)),
            "findings": findings,
        }, indent=2, ensure_ascii=False))
    else:
        print(f"status date: {consensus}")
        if not findings:
            print("no drift")
        for f in findings:
            print(f"[{f['severity']:6}] {f['class']:11} {f['detail']}\n{'':21}fix: {f['fix']}")
        print(f"\n{len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
