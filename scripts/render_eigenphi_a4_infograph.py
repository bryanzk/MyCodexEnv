#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from render_eigenphi_timeline import CATEGORY_COLORS, load_events


YEAR_THEMES = {
    2021: "起盘与资本验证",
    2022: "能力搭建与研究奠基",
    2023: "分发扩张与生态嵌入",
    2024: "跨链延展与内容产品化",
    2025: "观点输出与商业合作",
    2026: "风险研究外延",
}

PHASES = [
    {
        "label": "Phase 1",
        "years": "2021-2022",
        "title": "Foundation",
        "summary": "从平台上线、融资验证，到三明治/套利/清算识别与协议级研究报告成型。",
    },
    {
        "label": "Phase 2",
        "years": "2023-2024",
        "title": "Expansion",
        "summary": "产品基础设施升级，分发进入 DefiLlama / Etherscan / MetaMask 等外部入口，并扩展到 Solana。",
    },
    {
        "label": "Phase 3",
        "years": "2025-2026",
        "title": "Narrative + Data",
        "summary": "通过演讲、电子书与数据合作把研究能力向行业叙事与商业交付外溢。",
    },
]

CATEGORY_PRIORITY = {
    "产品/研究": 0,
    "产品": 1,
    "研究报告": 2,
    "研究": 2,
    "市场": 3,
    "未分类": 4,
}


def shorten(text: str, limit: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def select_highlights(year_events: list[dict], limit: int) -> list[dict]:
    ranked = sorted(
        year_events,
        key=lambda item: (
            CATEGORY_PRIORITY.get(item["category"], 9),
            item["start_month"],
            item["index"],
        ),
    )
    picks: list[dict] = []
    used_categories: set[str] = set()

    for item in ranked:
        if item["category"] in used_categories:
            continue
        picks.append(item)
        used_categories.add(item["category"])
        if len(picks) >= limit:
            return sorted(picks, key=lambda event: (event["start_month"], event["index"]))

    for item in ranked:
        if item in picks:
            continue
        picks.append(item)
        if len(picks) >= limit:
            break

    return sorted(picks, key=lambda event: (event["start_month"], event["index"]))


def build_year_sections(events: list[dict]) -> str:
    by_year: dict[int, list[dict]] = defaultdict(list)
    for item in events:
        by_year[item["year"]].append(item)

    cards: list[str] = []
    for year in sorted(by_year):
        year_events = by_year[year]
        year_counts = Counter(item["category"] for item in year_events)
        limit = 3 if len(year_events) >= 10 else 2
        highlights = select_highlights(year_events, limit)
        category_bits = []
        for category, count in sorted(year_counts.items(), key=lambda item: (-item[1], item[0])):
            palette = CATEGORY_COLORS.get(category, CATEGORY_COLORS["未分类"])
            category_bits.append(
                f'<span class="mini-badge" style="--accent:{palette["accent"]}; --soft:{palette["soft"]};">{html.escape(category)} {count}</span>'
            )
        bullet_html = []
        for item in highlights:
            bullet_html.append(
                f"""
                <li>
                  <span class="bullet-time">{html.escape(item["time"])}</span>
                  <span>{html.escape(shorten(item["headline"], 48))}</span>
                </li>
                """
            )

        cards.append(
            f"""
            <article class="year-card">
              <div class="year-top">
                <div>
                  <p class="year-label">{year}</p>
                  <h2>{html.escape(YEAR_THEMES.get(year, "Milestone Cluster"))}</h2>
                </div>
                <div class="event-total">
                  <strong>{len(year_events)}</strong>
                  <span>events</span>
                </div>
              </div>
              <div class="badge-row">
                {''.join(category_bits)}
              </div>
              <ul class="highlight-list">
                {''.join(bullet_html)}
              </ul>
            </article>
            """
        )

    return "\n".join(cards)


def build_timeline_strip(events: list[dict]) -> str:
    by_year: dict[int, list[dict]] = defaultdict(list)
    for item in events:
        by_year[item["year"]].append(item)

    parts: list[str] = []
    for year in sorted(by_year):
        counts = Counter(item["category"] for item in by_year[year])
        dominant = counts.most_common(1)[0][0]
        accent = CATEGORY_COLORS.get(dominant, CATEGORY_COLORS["未分类"])["accent"]
        parts.append(
            f"""
            <div class="year-node">
              <span class="node-dot" style="--accent:{accent};"></span>
              <div class="node-copy">
                <strong>{year}</strong>
                <span>{len(by_year[year])} milestones</span>
              </div>
            </div>
            """
        )
    return "\n".join(parts)


def build_phase_blocks(events: list[dict]) -> str:
    by_year: dict[int, list[dict]] = defaultdict(list)
    for item in events:
        by_year[item["year"]].append(item)

    blocks: list[str] = []
    for phase in PHASES:
        years = [int(part) for part in phase["years"].split("-")]
        phase_events = []
        for year in range(years[0], years[1] + 1):
            phase_events.extend(by_year.get(year, []))
        blocks.append(
            f"""
            <article class="phase-card">
              <p>{phase['label']}</p>
              <h3>{phase['title']}</h3>
              <strong>{phase['years']}</strong>
              <span>{len(phase_events)} milestones</span>
              <p class="phase-summary">{phase['summary']}</p>
            </article>
            """
        )
    return "\n".join(blocks)


def build_category_totals(events: list[dict]) -> str:
    total = len(events)
    counts = Counter(item["category"] for item in events)
    blocks: list[str] = []
    for category, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        palette = CATEGORY_COLORS.get(category, CATEGORY_COLORS["未分类"])
        width = max(12, round(count / total * 100))
        blocks.append(
            f"""
            <div class="category-row">
              <div class="category-head">
                <span class="legend-dot" style="--accent:{palette['accent']};"></span>
                <span>{html.escape(category)}</span>
              </div>
              <div class="bar-track">
                <span class="bar-fill" style="--accent:{palette['accent']}; width:{width}%"></span>
              </div>
              <strong>{count}</strong>
            </div>
            """
        )
    return "\n".join(blocks)


def render_html(events: list[dict], source_path: Path) -> str:
    first_year = min(item["year"] for item in events)
    last_year = max(item["year"] for item in events)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    category_counts = Counter(item["category"] for item in events)
    top_category, top_count = category_counts.most_common(1)[0]

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>EigenPhi Milestones A4 Infograph</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    @page {{
      size: A4 landscape;
      margin: 0;
    }}

    :root {{
      --paper: #f7f0e6;
      --panel: #fffaf3;
      --panel-2: #f2e7d7;
      --ink: #201a15;
      --muted: #6d5e50;
      --line: rgba(89, 61, 33, 0.16);
      --accent: #8c5a2b;
      --accent-2: #215f5b;
      --accent-3: #7f4477;
      --shadow: 0 12px 30px rgba(90, 62, 32, 0.1);
    }}

    * {{
      box-sizing: border-box;
    }}

    html, body {{
      margin: 0;
      padding: 0;
      background: #dfd4c5;
      color: var(--ink);
      font-family: "IBM Plex Sans", "PingFang SC", "Hiragino Sans GB", sans-serif;
    }}

    body {{
      padding: 8px;
    }}

    .sheet {{
      width: 297mm;
      min-height: 210mm;
      margin: 0 auto;
      padding: 8mm 9mm 6mm;
      background:
        radial-gradient(circle at top right, rgba(143, 94, 41, 0.16), transparent 20%),
        radial-gradient(circle at 18% 18%, rgba(33, 95, 91, 0.08), transparent 18%),
        linear-gradient(180deg, #faf3e9 0%, #f6ecdf 100%);
      overflow: hidden;
      position: relative;
      box-shadow: 0 22px 70px rgba(0, 0, 0, 0.18);
    }}

    .sheet::before {{
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(76, 52, 29, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(76, 52, 29, 0.03) 1px, transparent 1px);
      background-size: 14mm 14mm;
      mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.34), transparent 88%);
    }}

    .topbar {{
      display: grid;
      grid-template-columns: 1.8fr 1fr;
      gap: 6mm;
      align-items: start;
      position: relative;
      z-index: 1;
    }}

    .eyebrow {{
      margin: 0 0 2mm;
      font: 500 9px/1.2 "IBM Plex Mono", monospace;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: #9a7b5d;
    }}

    h1, h2, h3, p {{
      margin: 0;
    }}

    h1 {{
      max-width: 10ch;
      font-family: "DM Serif Display", Georgia, serif;
      font-size: 28px;
      line-height: 0.92;
      letter-spacing: -0.03em;
    }}

    .deck {{
      margin-top: 2mm;
      max-width: 80ch;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.45;
    }}

    .headline-panel {{
      padding: 0;
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2.5mm;
    }}

    .stat-card {{
      padding: 3.2mm 3.6mm;
      border-radius: 5mm;
      background: rgba(255, 250, 243, 0.88);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }}

    .stat-card strong {{
      display: block;
      font-family: "DM Serif Display", Georgia, serif;
      font-size: 21px;
      line-height: 0.95;
    }}

    .stat-card span {{
      display: block;
      margin-top: 1.4mm;
      color: var(--muted);
      font-size: 8.7px;
      line-height: 1.35;
    }}

    .timeline-strip {{
      margin-top: 3mm;
      padding: 3.2mm 4mm 2.8mm;
      border-radius: 6mm;
      background: rgba(255, 250, 243, 0.88);
      border: 1px solid var(--line);
      position: relative;
      box-shadow: var(--shadow);
    }}

    .timeline-strip::before {{
      content: "";
      position: absolute;
      left: 7mm;
      right: 7mm;
      top: 10mm;
      height: 1.2px;
      background: linear-gradient(90deg, rgba(140, 90, 43, 0.28), rgba(33, 95, 91, 0.34), rgba(127, 68, 119, 0.34));
    }}

    .timeline-nodes {{
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 2.4mm;
      position: relative;
      z-index: 1;
    }}

    .year-node {{
      display: grid;
      justify-items: center;
      gap: 1.4mm;
      text-align: center;
    }}

    .node-dot {{
      width: 11px;
      height: 11px;
      border-radius: 50%;
      background: var(--accent);
      background: var(--accent);
      box-shadow: 0 0 0 5px color-mix(in srgb, var(--accent) 16%, white);
      position: relative;
      z-index: 2;
    }}

    .node-dot {{
      background: var(--accent);
      background: var(--accent);
    }}

    .node-dot[style] {{
      background: var(--accent);
    }}

    .node-copy strong {{
      display: block;
      font: 600 10.2px/1.2 "IBM Plex Mono", monospace;
    }}

    .node-copy span {{
      display: block;
      color: var(--muted);
      font-size: 8px;
    }}

    .content-grid {{
      display: grid;
      grid-template-columns: 2.1fr 0.95fr;
      gap: 3mm;
      margin-top: 3mm;
      position: relative;
      z-index: 1;
    }}

    .year-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2.6mm;
      align-content: start;
    }}

    .year-card, .sidebar-card, .phase-card {{
      background: rgba(255, 250, 243, 0.92);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }}

    .year-card {{
      border-radius: 5mm;
      padding: 3.2mm;
      min-height: 38mm;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 1.8mm;
    }}

    .year-top {{
      display: flex;
      justify-content: space-between;
      gap: 2mm;
      align-items: start;
    }}

    .year-label {{
      font: 600 10px/1.2 "IBM Plex Mono", monospace;
      color: #9a7b5d;
      letter-spacing: 0.08em;
    }}

    .year-card h2 {{
      margin-top: 1mm;
      font-family: "DM Serif Display", Georgia, serif;
      font-size: 14px;
      line-height: 1.05;
    }}

    .event-total {{
      min-width: 14mm;
      padding: 1.8mm 2.2mm;
      border-radius: 4mm;
      background: var(--panel-2);
      text-align: center;
    }}

    .event-total strong {{
      display: block;
      font-family: "DM Serif Display", Georgia, serif;
      font-size: 18px;
      line-height: 0.92;
    }}

    .event-total span {{
      display: block;
      margin-top: 0.5mm;
      font-size: 7.5px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .badge-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 1mm;
    }}

    .mini-badge {{
      display: inline-flex;
      align-items: center;
      padding: 0.9mm 1.6mm;
      border-radius: 999px;
      background: var(--soft);
      color: color-mix(in srgb, var(--accent) 80%, black);
      font-size: 7.4px;
      line-height: 1.1;
      border: 1px solid color-mix(in srgb, var(--accent) 18%, white);
    }}

    .highlight-list {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 1.2mm;
      align-content: start;
    }}

    .highlight-list li {{
      display: grid;
      grid-template-columns: 14mm 1fr;
      gap: 1.4mm;
      font-size: 8px;
      line-height: 1.3;
      color: var(--ink);
      min-width: 0;
    }}

    .bullet-time {{
      color: var(--muted);
      font-family: "IBM Plex Mono", monospace;
      font-size: 7.2px;
    }}

    .sidebar {{
      display: grid;
      gap: 2.6mm;
      align-content: start;
    }}

    .sidebar-card {{
      border-radius: 5mm;
      padding: 3.2mm;
    }}

    .sidebar-card h3 {{
      font-family: "DM Serif Display", Georgia, serif;
      font-size: 14px;
      line-height: 1.05;
      margin-bottom: 2.4mm;
    }}

    .category-row {{
      display: grid;
      grid-template-columns: 16mm 1fr 8mm;
      gap: 1.6mm;
      align-items: center;
      margin-bottom: 1.5mm;
    }}

    .category-head {{
      display: flex;
      align-items: center;
      gap: 1.4mm;
      min-width: 0;
      font-size: 8px;
    }}

    .legend-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent);
      flex: 0 0 auto;
    }}

    .bar-track {{
      height: 7px;
      border-radius: 999px;
      background: rgba(89, 61, 33, 0.09);
      overflow: hidden;
    }}

    .bar-fill {{
      display: block;
      height: 100%;
      border-radius: inherit;
      background: var(--accent);
    }}

    .category-row strong {{
      justify-self: end;
      font: 600 8px/1 "IBM Plex Mono", monospace;
      color: var(--muted);
    }}

    .phase-grid {{
      display: grid;
      gap: 1.8mm;
      margin-top: 0.5mm;
    }}

    .phase-card {{
      border-radius: 4mm;
      padding: 2.6mm 2.8mm;
    }}

    .phase-card p:first-child {{
      font: 600 8px/1.2 "IBM Plex Mono", monospace;
      color: #9a7b5d;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}

    .phase-card h3 {{
      margin-top: 1mm;
      font-family: "DM Serif Display", Georgia, serif;
      font-size: 12.5px;
    }}

    .phase-card strong {{
      display: block;
      margin-top: 0.5mm;
      font: 600 7.8px/1.2 "IBM Plex Mono", monospace;
      color: var(--muted);
    }}

    .phase-card span {{
      display: block;
      margin-top: 0.5mm;
      font-size: 7.8px;
      color: var(--muted);
    }}

    .phase-summary {{
      margin-top: 1mm;
      font-size: 7.8px;
      line-height: 1.3;
      color: var(--ink);
    }}

    .footer {{
      margin-top: 2.4mm;
      padding-top: 1.6mm;
      border-top: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 3mm;
      font-size: 7.2px;
      color: var(--muted);
      position: relative;
      z-index: 1;
    }}

    code {{
      font-family: "IBM Plex Mono", monospace;
      font-size: 7px;
    }}

    @media screen and (max-width: 1300px) {{
      body {{
        padding: 0;
      }}

      .sheet {{
        width: 100vw;
        min-height: auto;
        box-shadow: none;
      }}
    }}

    @media print {{
      html, body {{
        width: 297mm;
        height: 210mm;
        overflow: hidden;
        background: transparent;
      }}

      body {{
        padding: 0;
      }}

      .sheet {{
        width: 297mm;
        height: 210mm;
        min-height: 210mm;
        margin: 0;
        box-shadow: none;
        overflow: hidden;
        break-after: avoid-page;
      }}
    }}
  </style>
</head>
<body>
  <main class="sheet">
    <section class="topbar">
      <div class="headline-panel">
        <p class="eyebrow">One-Page A4 Infograph</p>
        <h1>EigenPhi Milestones Condensed</h1>
        <p class="deck">
          把原始 38 条里程碑压成单页汇报版：用 6 个年度卡片概括 EigenPhi 从
          <strong>MEV 原生分析平台</strong> 到 <strong>研究权威 + 数据合作方</strong> 的演进路径，
          适合直接打印到 A4 landscape 或嵌入 deck。
        </p>
      </div>
      <div class="stats-grid">
        <article class="stat-card">
          <strong>{len(events)}</strong>
          <span>总里程碑数，覆盖 {first_year}-{last_year}</span>
        </article>
        <article class="stat-card">
          <strong>{last_year - first_year + 1}</strong>
          <span>连续年份，形成完整成长曲线</span>
        </article>
        <article class="stat-card">
          <strong>{top_count}</strong>
          <span>最大类别是 {html.escape(top_category)}</span>
        </article>
      </div>
    </section>

    <section class="timeline-strip">
      <p class="eyebrow">Chronology</p>
      <div class="timeline-nodes">
        {build_timeline_strip(events)}
      </div>
    </section>

    <section class="content-grid">
      <div class="year-grid">
        {build_year_sections(events)}
      </div>
      <aside class="sidebar">
        <section class="sidebar-card">
          <p class="eyebrow">Category Mix</p>
          <h3>结构分布</h3>
          {build_category_totals(events)}
        </section>
        <section class="sidebar-card">
          <p class="eyebrow">Evolution Arc</p>
          <h3>三阶段演进</h3>
          <div class="phase-grid">
            {build_phase_blocks(events)}
          </div>
        </section>
      </aside>
    </section>

    <footer class="footer">
      <span>Source: <code>{html.escape(str(source_path))}</code></span>
      <span>Generated: <code>{generated_at}</code></span>
      <span>Print hint: A4 landscape, scale 100%</span>
    </footer>
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a single-page A4 infograph from the EigenPhi milestones workbook.")
    parser.add_argument("input", nargs="?", default="/Users/kezheng/Downloads/EigenPhi Milestones.xlsx")
    parser.add_argument("output", nargs="?", default="tasks/eigenphi-milestones-a4-infograph.html")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    events = load_events(input_path)
    output_path.write_text(render_html(events, input_path), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
