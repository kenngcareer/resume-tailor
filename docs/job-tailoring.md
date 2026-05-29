# Job Tailoring Workflow

## Add a Job Posting

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

After review, change decisions in `bullet_review.yml`:

```yaml
decision: approved
```

or:

```yaml
decision: edited
user_edit: "Your revised bullet."
```

Then generate reviewed artifacts:

```powershell
py -m resume_tailor apply-approved outputs\example-job\bullet_review.yml
```

This writes:

- `resume_approved.md`
- `approval_summary.md`

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
