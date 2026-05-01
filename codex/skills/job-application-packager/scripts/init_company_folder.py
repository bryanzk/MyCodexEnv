#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


def safe_folder_name(company: str) -> str:
    cleaned = re.sub(r"[/:]+", "-", company.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or "Company"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a company folder and print output paths.")
    parser.add_argument("--company", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--candidate", default="Bryan Zheng")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser().resolve()
    folder = base_dir / safe_folder_name(args.company)
    folder.mkdir(parents=True, exist_ok=True)

    data = {
      "company": args.company,
      "role": args.role,
      "folder": str(folder),
      "resume_pdf": str(folder / f"{args.candidate} - {args.company} CV.pdf"),
      "answers_doc": str(folder / f"{args.company} application answers.md"),
    }
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
