# Job Tailoring Workflow

## Add a Job Posting

To try the product without private files, run:

```powershell
py -m resume_tailor demo
```

The demo uses fake data from `examples/demo/` and writes outputs under `demo-output/`.

Create a Markdown or text file under `private/job-postings/`.

Example:

```powershell
notepad private\job-postings\example-job.md
```

Paste the job description into that file.

## Generate Tailored Outputs

Start with the explainable analysis:

```powershell
py -m resume_tailor analyze-job private\job-postings\example-job.md --base-resume tpm
```

This writes:

- `jd_analysis.yml`
- `match_report.md`

Then generate tailoring artifacts:

```powershell
py -m resume_tailor tailor-job private\job-postings\example-job.md
```

The command writes two files under `outputs/<job-name>/`:

- `resume_draft.md`
- `tailoring_notes.md`

For a real application, use a private base resume:

```powershell
py -m resume_tailor tailor-job private\job-postings\example-job.md --base-resume tpm
```

or:

```powershell
py -m resume_tailor tailor-job private\job-postings\example-job.md --base-resume pm
```

This adds:

- `resume_tailored.md`
- `rewrite_plan.md`
- `verification_checklist.md`

For the guided review step, generate side-by-side bullet suggestions:

```powershell
py -m resume_tailor review-diff private\job-postings\example-job.md --base-resume tpm
```

This writes:

- `bullet_review.yml`
- `bullet_review.md`

Each review item includes the original bullet, suggested rewrite, related JD requirement, reason, supporting evidence, confidence label, and `pending` decision.

The review also includes truthfulness guardrail fields:

- `truthfulness_risk`
- `blocked_terms`
- `confirmation_prompt`

Treat medium/high risk items as confirmation prompts, not ready-to-use resume claims.

`apply-approved` enforces these fields:

- low-risk approved items are included
- medium-risk approved items require `confirmation_note`
- high-risk approved items require `override_truthfulness_block: true`
- edited bullets are rechecked before inclusion

After review, change decisions in `bullet_review.yml`:

```yaml
decision: approved
```

or:

```yaml
decision: edited
user_edit: "Your revised bullet."
```

For medium-risk items, add:

```yaml
confirmation_note: "Confirmed this wording is accurate."
```

For high-risk items, the default is to block. If you deliberately want to override:

```yaml
override_truthfulness_block: true
confirmation_note: "Confirmed this claim is accurate and supported."
```

Then generate reviewed artifacts:

```powershell
py -m resume_tailor apply-approved outputs\example-job\bullet_review.yml
```

This writes:

- `resume_approved.md`
- `approval_summary.md`
- `blocked_items.md`

Export the reviewed resume to an ATS-safe DOCX:

```powershell
py -m resume_tailor export-docx outputs\example-job\resume_approved.md
```

This writes:

- `resume_approved.docx`
- `resume_approved_export_summary.md`

## Review Rules

Treat the generated resume as a draft. Before applying:

- verify every metric and claim
- remove confidential details
- check whether the selected bullets actually answer the job posting
- adapt the wording into your preferred resume format

## Quality Bar

The first-pass generator is useful for matching and notes, but it should not replace a strong base resume. For real applications, use the output as tailoring guidance, then produce a polished version that preserves the structure, density, and strongest bullets from the relevant source resume.

For TPM roles, start from the TPM resume. For PM roles, start from the PM resume.

The current version is deterministic and local. It does not call an external AI service.
