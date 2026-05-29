# Architecture

## Principles

- Local-first: source materials stay on this laptop unless you intentionally connect an external model.
- Evidence-based: every resume bullet should map back to a real project, result, or colleague feedback.
- Human-reviewed: generated resumes are drafts, not final truth.
- Reusable profile: keep one structured career profile and tailor from that, instead of rewriting from scratch every time.

## Core Objects

### Career Profile

The normalized source of truth for your experience:

- roles
- projects
- skills
- industries
- measurable outcomes
- leadership examples
- feedback snippets
- preferred positioning

### Job Posting

The target role:

- company
- title
- responsibilities
- required skills
- preferred skills
- keywords
- signals about level, scope, and domain

### Tailoring Plan

The strategy for the application:

- strongest matching themes
- resume sections to emphasize
- keywords to include naturally
- experience to downplay
- gaps or risks

### Resume Draft

The generated artifact:

- summary
- selected experience bullets
- skills
- optional cover letter notes
- verification checklist

## Pipeline

1. Ingest source materials.
2. Extract evidence into `private/profile.yml`.
3. Parse a job posting.
4. Match job needs to career evidence.
5. Generate a tailoring plan.
6. Draft the resume.
7. Produce a rationale and verification checklist.
