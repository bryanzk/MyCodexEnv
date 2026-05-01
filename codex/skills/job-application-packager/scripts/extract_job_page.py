#!/usr/bin/env python3
import argparse
import html
import json
import re
import sys
import urllib.request
from typing import List, Optional


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_tags(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", value, flags=re.S)
    no_tags = html.unescape(no_tags)
    return re.sub(r"\s+", " ", no_tags).strip()


def first_match(pattern: str, text: str, flags: int = re.I | re.S) -> Optional[str]:
    m = re.search(pattern, text, flags)
    if not m:
        return None
    return m.group(1).strip()


def unique(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def parse_company_and_role(title: str) -> tuple[Optional[str], Optional[str]]:
    title = title.strip()
    if " - " in title:
        left, right = title.split(" - ", 1)
        if left and right:
            return left.strip(), right.strip()
    return None, title or None


def extract_fields(html_text: str) -> List[str]:
    patterns = [
        r'<div class="application-label[^"]*">(.*?)</div>',
        r'<div class="text">(.*?)<span class="required">',
        r"<label[^>]*>\s*<div class=\"application-label[^>]*\">(.*?)</div>",
    ]
    fields: List[str] = []
    for pattern in patterns:
        for raw in re.findall(pattern, html_text, re.I | re.S):
            label = strip_tags(raw)
            if label:
                fields.append(label)
    return unique(fields)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract job/apply page basics from a URL.")
    parser.add_argument("url")
    args = parser.parse_args()

    html_text = fetch_html(args.url)
    title = first_match(r"<title>(.*?)</title>", html_text) or ""
    og_title = first_match(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html_text) or ""
    twitter_desc = (
        first_match(r'<meta[^>]+name="twitter:description"[^>]+content="([^"]+)"', html_text) or ""
    )
    headline = first_match(r'<h2[^>]*class="posting-headline"[^>]*>(.*?)</h2>', html_text)
    company, role = parse_company_and_role(og_title or title)

    data = {
        "source_url": args.url,
        "detected_board": "lever" if "jobs.lever.co" in args.url else "generic",
        "title": strip_tags(og_title or title or headline or ""),
        "company": company,
        "role": strip_tags(headline or role or ""),
        "summary": strip_tags(twitter_desc),
        "fields": extract_fields(html_text),
    }
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
