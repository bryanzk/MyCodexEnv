#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_CHROME = (
    Path.home()
    / "Library/Caches/ms-playwright/chromium_headless_shell-1223"
    / "chrome-headless-shell-mac-arm64/chrome-headless-shell"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a Mermaid flowchart from an HTML page by extracting the rendered SVG and screenshotting it at the SVG's full height."
    )
    parser.add_argument("input_html", help="Path to the source HTML page")
    parser.add_argument("output_png", help="Path to the output PNG")
    parser.add_argument("--chrome", default=str(DEFAULT_CHROME), help="Path to the headless Chrome binary")
    parser.add_argument("--width", type=int, default=1182, help="Target PNG width in CSS pixels before device scale factor")
    parser.add_argument("--padding", type=int, default=34, help="Outer padding around the SVG in CSS pixels")
    parser.add_argument("--scale", type=int, default=1, choices=(1, 2), help="Device scale factor")
    parser.add_argument("--background", default="#f7faf7", help="Background color for the export canvas")
    parser.add_argument("--watermark", default="ShipAI.ca", help="Watermark text. Use empty string to disable")
    return parser.parse_args()


def dump_dom(chrome: Path, input_html: Path) -> str:
    tmp_dir = Path(tempfile.mkdtemp(prefix="mermaid-export-dom-"))
    try:
        result = subprocess.run(
            [
                str(chrome),
                "--headless=new",
                "--disable-gpu",
                "--disable-background-networking",
                "--no-first-run",
                f"--user-data-dir={tmp_dir}",
                "--virtual-time-budget=8000",
                "--dump-dom",
                input_html.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        return result.stdout
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def extract_svg(html: str) -> tuple[str, float, float]:
    svg_match = re.search(r"(<svg[\s\S]*?</svg>)", html)
    if not svg_match:
        raise RuntimeError("rendered Mermaid SVG not found in dumped DOM")

    svg = svg_match.group(1)
    viewbox_match = re.search(r'viewBox="([0-9.\s-]+)"', svg)
    if not viewbox_match:
        raise RuntimeError("SVG viewBox not found")

    values = [float(part) for part in viewbox_match.group(1).split()]
    if len(values) != 4:
        raise RuntimeError("SVG viewBox does not contain four numeric values")

    _, _, width, height = values
    return svg, width, height


def build_export_html(svg: str, canvas_width: int, canvas_height: int, inner_width: int, watermark: str, background: str) -> str:
    watermark_html = ""
    if watermark:
        watermark_html = f'<div class="watermark">{watermark}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0;
      width: {canvas_width}px;
      height: {canvas_height}px;
      overflow: hidden;
      background: {background};
    }}
    body {{
      position: relative;
      padding: 34px;
      font-family: "Atkinson Hyperlegible", Verdana, sans-serif;
    }}
    .stage {{
      width: {inner_width}px;
      margin: 0 auto;
    }}
    .stage svg {{
      display: block;
      width: {inner_width}px;
      height: auto;
    }}
    .watermark {{
      position: absolute;
      right: 18px;
      bottom: 12px;
      color: #0f9b8e;
      opacity: 0.48;
      font: 600 12px "IBM Plex Mono", monospace;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
  </style>
</head>
<body>
  <div class="stage">
    {svg}
  </div>
  {watermark_html}
</body>
</html>
"""


def screenshot_export(chrome: Path, html_path: Path, output_png: Path, width: int, height: int, scale: int) -> None:
    tmp_dir = Path(tempfile.mkdtemp(prefix="mermaid-export-shot-"))
    try:
        subprocess.run(
            [
                str(chrome),
                "--headless=new",
                "--disable-gpu",
                "--disable-background-networking",
                "--no-first-run",
                f"--user-data-dir={tmp_dir}",
                f"--window-size={width},{height}",
                f"--force-device-scale-factor={scale}",
                "--screenshot=" + str(output_png.resolve()),
                html_path.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> int:
    args = parse_args()
    chrome = Path(args.chrome).expanduser()
    input_html = Path(args.input_html)
    output_png = Path(args.output_png)

    if not chrome.exists():
      raise SystemExit(f"ERROR: chrome binary not found: {chrome}")
    if not input_html.exists():
      raise SystemExit(f"ERROR: input html not found: {input_html}")

    html = dump_dom(chrome, input_html)
    svg, view_width, view_height = extract_svg(html)

    inner_width = args.width - (args.padding * 2)
    scale_ratio = inner_width / view_width
    export_height = math.ceil((view_height * scale_ratio) + (args.padding * 2))

    export_html = build_export_html(
        svg=svg,
        canvas_width=args.width,
        canvas_height=export_height,
        inner_width=inner_width,
        watermark=args.watermark,
        background=args.background,
    )

    tmp_html = Path(tempfile.mkdtemp(prefix="mermaid-export-html-")) / "export.html"
    try:
        tmp_html.write_text(export_html, encoding="utf-8")
        output_png.parent.mkdir(parents=True, exist_ok=True)
        screenshot_export(
            chrome=chrome,
            html_path=tmp_html,
            output_png=output_png,
            width=args.width,
            height=export_height,
            scale=args.scale,
        )
    finally:
        shutil.rmtree(tmp_html.parent, ignore_errors=True)

    print(
        f"exported {output_png} from {input_html} "
        f"(viewBox={view_width:.2f}x{view_height:.2f}, css={args.width}x{export_height}, scale={args.scale})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
