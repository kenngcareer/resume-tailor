# Resume Tailor

Resume Tailor is a local-first career portfolio assistant. It helps turn a job posting plus your verified career evidence into a customized resume draft for that role.

The goal is not to invent experience. The goal is to pick the strongest truthful evidence, adjust language to the role, and produce a resume that is easy for recruiters and hiring managers to map to the job.

For real applications, the strongest path is to start from the best existing resume version and tailor it. The generated Markdown draft is a matching aid and review artifact, not automatically the final resume.

## MVP Workflow

1. Add private source material under `private/source-materials/`.
2. Create or update your normalized career profile at `private/profile.yml`.
3. Save a job posting in `private/job-postings/`.
4. Run the tailor workflow with `py -m resume_tailor tailor-job private\job-postings\your-job.md`.
5. Review the generated resume and rationale in `outputs/`.

## Source Materials

Useful inputs include:

- PM and TPM resume versions
- Career portfolio documents
- Peer and manager feedback
- LinkedIn profile export or copy
- Project writeups
- STAR stories
- Promotion packets or performance review excerpts

Keep raw source material private. This repo is configured so `private/` and `outputs/` are not committed by default.

## What This Should Produce

For each job, the tool should generate:

- A customized resume draft
- A concise tailoring rationale
- A gap analysis
- Suggested interview story themes
- A checklist of claims that need human verification

## Current Status

This repo has a first-pass offline workflow for extracting PDF text, building a private profile draft, and generating job-specific resume drafts.

## Commands

```powershell
py -m resume_tailor init-private
py -m resume_tailor extract-sources
py -m resume_tailor build-profile
py -m resume_tailor inspect-profile private\profile.yml
py -m resume_tailor tailor-job private\job-postings\your-job.md
py -m resume_tailor tailor-job private\job-postings\your-job.md --base-resume tpm
```
