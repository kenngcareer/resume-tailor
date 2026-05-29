# Job Tailoring Workflow

## Add a Job Posting

Create a Markdown or text file under `private/job-postings/`.

Example:

```powershell
notepad private\job-postings\example-job.md
```

Paste the job description into that file.

## Generate Tailored Outputs

```powershell
py -m resume_tailor tailor-job private\job-postings\example-job.md
```

The command writes two files under `outputs/<job-name>/`:

- `resume_draft.md`
- `tailoring_notes.md`

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
