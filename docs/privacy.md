# Privacy Model

This repository should assume career material is sensitive.

## Defaults

- `private/` is ignored by git.
- `outputs/` is ignored by git.
- Prompts and code are safe to commit.
- Raw resumes, feedback, LinkedIn exports, and generated drafts should not be committed unless you explicitly decide otherwise.

## Recommended Folder Layout

```text
private/
  profile.yml
  source-materials/
    resumes/
    linkedin/
    colleague-feedback/
    portfolio/
  job-postings/
outputs/
```

## External AI Use

If this project later connects to an external LLM API, add a clear switch that controls what content is sent. The safest default is to require explicit confirmation before sending private career material outside the machine.
