---
name: pdf-resume-format
description: Use when editing or QA'ing an existing resume/CV source or PDF for job applications, especially requests about PDF readability, clickable links, clean HTML-to-PDF export, natural role-fit wording, dense sections, header/footer artifacts, or avoiding “too made-up / too overdone” phrasing. Do not use for creating a full application package from a job URL; use job-application-packager instead.
---

# PDF Resume Format

## Purpose

Use this skill to make existing application PDFs readable, natural, factual, clickable, and professionally exported. It is especially useful after a tailored resume already exists in HTML, Markdown, DOCX, or PDF form.

## Workflow

1. Identify the review target: source file, output PDF, role/company, and exact user comments.
2. Edit the source artifact first when available (`.html`, `.md`, `.docx`), then regenerate the PDF. Do not hand-edit only the PDF unless no source exists.
3. Make the first page scannable:
   - Prefer 2-4 short bullets over one dense summary paragraph.
   - Lead with the strongest role-specific proof, not a generic objective.
   - Keep community/company/project evidence concise unless it is the main job requirement.
4. Keep role fit natural:
   - Avoid headings like `Role Alignment: <JD Deliverables>` when they feel like a checklist.
   - Prefer headings like `Relevant Experience for This Project`, `Relevant Experience`, or `Project Fit`.
   - Phrase transferable experience from the past: “mapped messy workflows,” “compared options,” “turned needs into PRDs,” “tested prototypes.”
   - Do not imply the candidate already completed the employer’s deliverables.
5. Keep claims factual:
   - Use only public links, source CV facts, or user-confirmed facts.
   - If a section is a capability mapping, make that clear with wording such as “experience supports.”
   - Remove unsupported artifacts or methods that sound inflated, even if they improve keyword match.
6. Improve readability:
   - Break keyword-heavy lines into grouped bullets.
   - Replace long comma lists with named groups such as `Community and research`, `Product delivery`, `Access and governance`, `Technical execution`.
   - Keep repeated sections short; if evidence already appears in Summary, do not repeat it at full length.
7. Make links clickable:
   - Wrap visible URLs with `<a href="https://...">display-url</a>` in HTML sources.
   - Prefer stable public profile/archive URLs over temporary site URLs when the user identifies the preferred destination.
   - Verify PDF link annotations, not just visible text.
8. Export cleanly:
   - For Chrome HTML-to-PDF, use `--no-pdf-header-footer`.
   - Ensure the PDF has no browser timestamp, title header, local `file:///` URL, or `/Users/...` path.
9. Run verification before claiming completion.

## Chrome Export Pattern

```bash
'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
  --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf='/abs/path/output.pdf' \
  'file:///abs/path/source.html'
```

## Verification

Use `scripts/check_resume_pdf.py` for deterministic checks. If default `python3` lacks `pypdf`, call `load_workspace_dependencies` and run the script with the bundled Python executable.

```bash
python3 /Users/kezheng/.codex/skills/pdf-resume-format/scripts/check_resume_pdf.py \
  '/abs/path/resume.pdf' \
  --require-text 'Relevant Experience for This Project' \
  --require-uri 'https://www.meetup.com/Startup4Chinese/' \
  --forbid-text 'file:///' \
  --forbid-text '/Users/'
```

Also run `qpdf --check /abs/path/resume.pdf` when available.

Final responses for PDF changes must include:

- `command`
- `exit_code`
- `key_output`
- `timestamp`

## Common Fixes

- Dense summary paragraph: convert to 3 bullets with bold labels.
- “Too 做作” role-fit section: rename and rewrite from past experience, not JD deliverables.
- Overlong community section: keep metrics and effect, remove operational details unless the role asks for community operations.
- Non-clickable visible URL: add `<a href>` and verify `/Annots` URI in PDF.
- Browser export artifacts: re-export with `--no-pdf-header-footer`.

## Boundary

- If the user gives a job URL and wants a tailored resume plus answers, use `job-application-packager` first. Use this skill only for the final resume PDF/source polish and verification.
- If the user asks to translate a PDF, use `pdf-translation`.
- If the user asks for generic document editing unrelated to resume/CV PDF polish, do not load this skill.
