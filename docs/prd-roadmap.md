# PRD Roadmap

This roadmap maps the current repo to the ResumeTailor AI v1.0 PRD.

## Implemented

- Local-first private source storage.
- PDF text extraction from private source materials.
- Initial profile draft generation.
- Job-specific tailoring notes and draft outputs.
- Base-resume-aware tailoring artifacts.
- Structured JD analysis.
- Explainable match report with strengths, partial matches, missing evidence, and confidence labels.
- Side-by-side bullet diff workflow with pending review decisions.
- Approved/edited review item application into reviewed resume artifacts.
- Truthfulness guardrail fields for risky rewrites, blocked terms, and confirmation prompts.
- Enforced approval blocking for medium/high truthfulness risk.
- ATS-safe DOCX export from reviewed Markdown resumes.
- Public demo workflow using fake profile, resume, and job posting data.
- Section-level reconstructed resume draft from approved review items.
- GitHub Actions CI.

## Next

- Stronger bullet rewrite generation.
- Optional LLM adapter with explicit privacy controls.
- Web UI for approve/reject/edit review.

## Product Direction

The product should not generate a final resume immediately. The core experience should be a guided review loop where every suggested change includes:

- original resume evidence
- suggested rewrite
- related JD requirement
- reason for the change
- confidence label
- user decision
