---
name: job-application-packager
description: Use when a user provides a job posting page or application form page and wants a company-specific application package generated from that page, including a tailored PDF resume and a field-by-field answer document based on the role, company, and visible form questions.
---

# Job Application Packager

## Overview

Turn a job page or application form page into a company-specific application package. The default deliverables are:

Before writing resume bullets, application answers, or delivery summaries, read and follow [TERMS.md](TERMS.md). Use those terms to keep the package concrete and role-specific instead of generic.

- a company-named folder
- one tailored PDF resume for that role
- one field-by-field answer document for the visible application form

Do not submit the application. Stop after generating the artifacts the user can review and use elsewhere.

## Workflow

### 1. Intake the page

- If the user gives a URL, inspect the live page first.
- If the page is public, prefer extracting the role, company, and form fields directly from that page.
- If the page is behind auth or rendered in a browser-only context, use the best available browser or app tools to inspect the visible form.
- For static or semi-static job boards, start with:
  ```bash
  python3 ~/.codex/skills/job-application-packager/scripts/extract_job_page.py "<JOB_URL>"
  ```

### 2. Create the company folder

- Create a company-named folder in the current workspace unless the user asks for another base directory.
- Keep the folder name company-first, not role-first.
- Use:
  ```bash
  python3 ~/.codex/skills/job-application-packager/scripts/init_company_folder.py \
    --company "<COMPANY>" \
    --role "<ROLE>" \
    --base-dir "$PWD"
  ```
- The script prints the folder path and the recommended output file names.

### 3. Build the role-specific resume

- Start from the strongest existing source resume in the workspace.
- Preserve real experience and measured outcomes; do not invent platform experience or customer ownership that is not supported.
- Reorder and rewrite bullets toward the target role. For application/solution architecture roles, prioritize:
  - workflow discovery
  - translating messy expert logic into deployable AI workflows
  - cross-functional delivery
  - reusable systems, guardrails, and operating patterns
  - enterprise-facing technical communication
- Keep language concise and natural. Avoid resume prose that reads inflated or AI-generated.
- Default working flow:
  1. create a tailored markdown or HTML source in the company folder
  2. export a PDF
  3. keep only the final PDF unless the user wants source files preserved

### 4. Export the PDF resume

- Prefer HTML-to-PDF export when layout quality matters.
- A reliable default on this machine is Chrome headless:
  ```bash
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
    --headless --disable-gpu \
    --print-to-pdf='/abs/path/output.pdf' \
    'file:///abs/path/source.html'
  ```
- Verify the PDF exists and, when practical, verify page count.

### 5. Write the field-by-field answer document

- Read the visible form fields exactly as presented on the page.
- Create one answer document in the company folder that lists each field and the recommended answer.
- Separate fields into two categories:
  - `Ready to fill`
  - `Needs user confirmation`
- Put the following into `Needs user confirmation` unless the user already provided the exact answer:
  - phone
  - work authorization
  - sponsorship
  - relocation
  - salary expectations
  - demographic or compliance questionnaires
- For free-text role-fit questions, align the answer doc with the tailored resume narrative.

### 6. Deliver the package

- The minimum final outputs in the company folder are:
  - one tailored PDF resume
  - one field-by-field answer document
- If you created working files such as `.md` or `.html`, remove them unless the user asked to keep editable sources.
- Do not fill or submit the form. The user explicitly uses Claude to do the actual page entry.

## Output conventions

- Folder name: company only, readable, sanitized for filesystem use
- Resume file: `<Candidate> - <Company> CV.pdf`
- Answers file: `<Company> application answers.md`
- Keep absolute paths in status updates so the generated files are easy to open

## Scripts

### `scripts/extract_job_page.py`

- Fetch a public job or application page
- Extract company, role, title, description, and visible form labels
- Prefer this as the first pass for Lever-style pages and other static HTML pages

### `scripts/init_company_folder.py`

- Normalize the company name into a safe folder name
- Create the company folder
- Print recommended output paths for the PDF resume and answer document

## Common mistakes

- Do not optimize for one-page resumes at the expense of relevance. If a second page carries real role-specific evidence, keep it.
- Do not invent experience with Zendesk, Salesforce, ServiceNow, or classic post-sales ownership unless it is real.
- Do not copy the raw form wording into the resume. The resume and answer document serve different purposes.
- Do not include browser-filling steps in the output package. This skill stops at artifact generation.
