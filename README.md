# Resume Tailor

[![CI](https://github.com/kenngcareer/resume-tailor/actions/workflows/ci.yml/badge.svg)](https://github.com/kenngcareer/resume-tailor/actions/workflows/ci.yml)

Resume Tailor is a local-first resume tailoring workflow for job seekers who want customized resumes without invented claims.

It turns a job posting plus verified career evidence into an explainable, reviewable, ATS-safe resume draft. The product thesis is simple: users will trust the resume tool that shows exactly why each change was suggested and blocks unsupported claims before they reach the final resume.

## Why This Exists

Generic AI resume tools can write fluent bullets, but they often blur the line between stronger framing and dishonest inflation. Resume Tailor is designed around two differentiators:

- Truth-preserving tailoring: suggestions are grounded in source resume/profile evidence.
- Explainable review: every suggested bullet rewrite includes the original bullet, related job requirement, reason, supporting evidence, confidence label, and approval state.

## Quick Demo

Run the full workflow with fake public data:

```powershell
py -m pip install -e .[dev]
py -m resume_tailor demo
```

Demo inputs live in `examples/demo/`. Generated demo artifacts are written to `demo-output/` and ignored by git.

## Workflow

```text
Job posting + base resume + profile
        |
        v
JD analyzer
        |
        v
Explainable match report
        |
        v
Side-by-side bullet review
        |
        v
Approve / reject / edit
        |
        v
Truthfulness guardrail
        |
        v
Approved Markdown resume
        |
        v
ATS-safe DOCX export
```

## Current Features

- PDF text extraction for private source materials.
- Structured private career profile generation.
- Job description analyzer for requirements, responsibilities, tools, seniority signals, and keywords.
- Explainable match report with score, strengths, partial matches, and missing evidence.
- Base-resume-aware tailoring artifacts.
- Side-by-side bullet review workflow.
- Truthfulness guardrails for risky rewrites.
- Enforced approval blocking for medium/high risk claims.
- Approved resume Markdown generation.
- ATS-safe DOCX export.
- Public fake-data demo.
- GitHub Actions CI.

## Core Commands

```powershell
py -m resume_tailor init-private
py -m resume_tailor demo
py -m resume_tailor extract-sources
py -m resume_tailor build-profile
py -m resume_tailor inspect-profile private\profile.yml
py -m resume_tailor analyze-job private\job-postings\your-job.md --base-resume tpm
py -m resume_tailor review-diff private\job-postings\your-job.md --base-resume tpm
py -m resume_tailor apply-approved outputs\your-job\bullet_review.yml
py -m resume_tailor export-docx outputs\your-job\resume_approved.md
```

## Privacy Model

The repo is designed to keep real career data local:

- `private/` is ignored by git.
- `outputs/` is ignored by git.
- `demo-output/` is ignored by git.
- Public examples use fake data only.

Raw resumes, LinkedIn exports, colleague feedback, generated tailored resumes, and job-specific outputs should stay in ignored local folders unless intentionally sanitized for public sharing.

See [docs/privacy.md](docs/privacy.md).

## Review Item Shape

The guided review workflow creates items like:

```yaml
original_bullet: Led launch governance across product and engineering.
suggested_rewrite: Led launch governance aligned to executive communication and risk management needs.
related_jd_requirement: Ability to lead executive communication and risk management.
reason_for_change: This bullet already has relevant evidence.
supporting_evidence: executive, risk
confidence: Strong
truthfulness_risk: low
blocked_terms: []
confirmation_prompt: ''
decision: pending
user_edit: ''
```

Approved and edited items can be applied into a reviewed resume. Medium-risk items require a confirmation note. High-risk items are blocked unless explicitly overridden.

## Project Docs

- [Architecture](docs/architecture.md)
- [Job tailoring workflow](docs/job-tailoring.md)
- [Privacy model](docs/privacy.md)
- [PRD roadmap](docs/prd-roadmap.md)

## Roadmap

- Public sample output snapshots.
- Stronger bullet rewrite generation.
- Better section-level resume reconstruction.
- Optional LLM adapter with explicit privacy controls.
- Render-based DOCX visual QA when LibreOffice is available.
- Web UI for approve/reject/edit review.
