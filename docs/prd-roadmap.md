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

## Next

- Truthfulness guardrail for unsupported rewrites.
- Approve, reject, and edit review state.
- ATS-safe DOCX export.
- Public demo using fake resume and fake job data.

## Product Direction

The product should not generate a final resume immediately. The core experience should be a guided review loop where every suggested change includes:

- original resume evidence
- suggested rewrite
- related JD requirement
- reason for the change
- confidence label
- user decision
