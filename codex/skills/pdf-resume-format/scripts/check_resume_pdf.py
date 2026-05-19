#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys


def read_pdf(path: Path):
    try:
        from pypdf import PdfReader
    except Exception as exc:
        print(f"ERROR: pypdf unavailable: {exc}")
        return None, "", []

    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    uris = []
    for page in reader.pages:
        for annot_ref in page.get("/Annots") or []:
            annot = annot_ref.get_object()
            action = annot.get("/A")
            if action and action.get("/URI"):
                uris.append(str(action.get("/URI")))
    return len(reader.pages), text, uris


def main():
    parser = argparse.ArgumentParser(description="Check resume PDF text, links, and export artifacts.")
    parser.add_argument("pdf")
    parser.add_argument("--require-text", action="append", default=[])
    parser.add_argument("--forbid-text", action="append", default=["file:///", "/Users/"])
    parser.add_argument("--require-uri", action="append", default=[])
    parser.add_argument("--min-pages", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=4)
    args = parser.parse_args()

    pdf = Path(args.pdf)
    if not pdf.exists():
        print(f"ERROR: missing PDF: {pdf}")
        return 1

    pages, text, uris = read_pdf(pdf)
    if pages is None:
        return 2

    failures = []
    low = text.lower()
    if not (args.min_pages <= pages <= args.max_pages):
        failures.append(f"page_count {pages} outside {args.min_pages}-{args.max_pages}")

    for needle in args.require_text:
        if needle.lower() not in low:
            failures.append(f"missing text: {needle}")

    for needle in args.forbid_text:
        if needle.lower() in low:
            failures.append(f"forbidden text present: {needle}")

    for uri in args.require_uri:
        if uri not in uris:
            failures.append(f"missing uri: {uri}")

    print(f"pdf={pdf}")
    print(f"exists={pdf.exists()}")
    print(f"size={pdf.stat().st_size}")
    print(f"pages={pages}")
    print(f"text_chars={len(text)}")
    print(f"uri_count={len(uris)}")
    for uri in uris:
        print(f"uri={uri}")

    if failures:
        print("status=fail")
        for failure in failures:
            print(f"failure={failure}")
        return 1

    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
