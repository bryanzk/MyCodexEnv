# pdf-resume-format Eval Matrix

## Existence

Keep this skill because repeated failures were observed during resume PDF polishing:

- dense first-page summary paragraphs
- artificial role-fit/JD checklist sections
- over-expanded community evidence
- non-clickable visible URLs
- browser PDF headers/footers and local file paths
- missing PDF annotation verification

## Positive Routing

Use this skill:

- "Make this resume PDF easier to read."
- "The Role Alignment section feels too 做作; rewrite it naturally."
- "Make the URLs in this CV PDF clickable."
- "Remove browser header/footer and local file path from this resume PDF."
- "Polish the existing CV HTML/PDF without inventing experience."

## Negative Routing

Do not use this skill:

- "Write a resume for this job link based on my previous CV." Use `job-application-packager`.
- "Translate this PDF book into Chinese." Use `pdf-translation`.
- "Extract tables from this PDF invoice." Use general PDF/data tooling.
- "Create a slide deck from this resume." Use presentation/document tools as appropriate.

## Forbidden Loads

Loading is harmful when:

- The task is the initial job-page intake and company package generation.
- The request is unrelated to resumes/CVs.
- The request is to submit or upload an application in a browser.

## Progressive Loading

Accessory: `scripts/check_resume_pdf.py`

- Trigger: after regenerating or editing a resume PDF.
- Evidence: output includes page count, text chars, URI list, and `status=pass`.
- Non-trigger: user asks only for high-level copy advice and no PDF exists.

## End-to-End Assertions

For a representative resume PDF/source edit, success requires:

- Dense summary becomes scannable bullets or short paragraphs.
- Role-fit section is natural and grounded in past experience.
- Unsupported claims are removed or softened.
- User-specified URLs are visible and clickable in PDF annotations.
- PDF text does not include local `file:///` or `/Users/...` paths.
- Final response reports fresh `command`, `exit_code`, `key_output`, and `timestamp`.
