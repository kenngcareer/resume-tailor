from pathlib import Path
import re

import click
import yaml
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRIVATE_ROOT = PROJECT_ROOT / "private"
SOURCE_ROOT = PRIVATE_ROOT / "source-materials"
EXTRACTED_ROOT = PRIVATE_ROOT / "extracted"
JOB_POSTINGS_ROOT = PRIVATE_ROOT / "job-postings"
OUTPUTS_ROOT = PROJECT_ROOT / "outputs"


@click.group()
def main() -> None:
    """Resume tailoring workflow commands."""


@main.command()
def init_private() -> None:
    """Create private local folders for source materials and outputs."""
    folders = [
        PROJECT_ROOT / "private" / "source-materials" / "resumes",
        PROJECT_ROOT / "private" / "source-materials" / "linkedin",
        PROJECT_ROOT / "private" / "source-materials" / "colleague-feedback",
        PROJECT_ROOT / "private" / "source-materials" / "portfolio",
        PROJECT_ROOT / "private" / "job-postings",
        PROJECT_ROOT / "outputs",
    ]
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    profile_path = PROJECT_ROOT / "private" / "profile.yml"
    if not profile_path.exists():
        profile_path.write_text(
            "name: ''\ntarget_roles: []\npositioning:\n  headline: ''\n  themes: []\nroles: []\nprojects: []\nfeedback: []\n",
            encoding="utf-8",
        )

    click.echo("Private folders are ready.")


@main.command()
@click.argument("profile_path", type=click.Path(exists=True, path_type=Path))
def inspect_profile(profile_path: Path) -> None:
    """Print a quick summary of a structured career profile."""
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    roles = profile.get("roles", [])
    projects = profile.get("projects", [])
    feedback = profile.get("feedback", [])
    documents = profile.get("documents", [])
    evidence = profile.get("evidence_snippets", [])
    feedback_themes = profile.get("feedback_themes", [])

    click.echo(f"Name: {profile.get('name', '')}")
    click.echo(f"Target roles: {', '.join(profile.get('target_roles', []))}")
    click.echo(f"Roles: {len(roles)}")
    click.echo(f"Projects: {len(projects)}")
    click.echo(f"Feedback entries: {len(feedback)}")
    click.echo(f"Source documents: {len(documents)}")
    click.echo(f"Evidence snippets: {len(evidence)}")
    click.echo(f"Feedback themes: {len(feedback_themes)}")


@main.command()
def extract_sources() -> None:
    """Extract searchable text from private PDF source materials."""
    pdf_paths = sorted(SOURCE_ROOT.rglob("*.pdf"))
    if not pdf_paths:
        raise click.ClickException(f"No PDF files found under {SOURCE_ROOT}")

    EXTRACTED_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = []

    for pdf_path in pdf_paths:
        relative = pdf_path.relative_to(SOURCE_ROOT)
        output_path = EXTRACTED_ROOT / relative.with_suffix(".txt")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        reader = PdfReader(str(pdf_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(pages).strip()
        output_path.write_text(text + "\n", encoding="utf-8")

        manifest.append(
            {
                "source": str(relative).replace("\\", "/"),
                "text": str(output_path.relative_to(PRIVATE_ROOT)).replace("\\", "/"),
                "pages": len(reader.pages),
                "characters": len(text),
            }
        )

    manifest_path = EXTRACTED_ROOT / "manifest.yml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    click.echo(f"Extracted {len(pdf_paths)} PDFs into {EXTRACTED_ROOT}")


@main.command()
def build_profile() -> None:
    """Build an initial career profile draft from extracted private sources."""
    text_paths = sorted(path for path in EXTRACTED_ROOT.rglob("*.txt") if path.name != "manifest.txt")
    if not text_paths:
        raise click.ClickException("No extracted text found. Run extract-sources first.")

    documents = []
    combined_sections = []
    for text_path in text_paths:
        text = text_path.read_text(encoding="utf-8")
        relative = text_path.relative_to(EXTRACTED_ROOT)
        documents.append(_document_summary(relative, text))
        combined_sections.append(text)

    combined_text = "\n".join(combined_sections)
    profile = {
        "name": _first_match(combined_text, r"\bKEN\s+NG\b", default="Ken Ng").title(),
        "target_roles": [
            "Product Manager",
            "Technical Program Manager",
            "AI Product Manager",
            "AI Technical Program Manager",
        ],
        "positioning": {
            "headline": _best_headline(combined_text),
            "themes": _ranked_themes(combined_text),
        },
        "documents": documents,
        "skills": _ranked_skills(combined_text),
        "evidence_snippets": _evidence_snippets(combined_text),
        "feedback_themes": _feedback_themes(combined_text),
        "verification_needed": [
            "Confirm exact metrics before using them in a tailored resume.",
            "Confirm which projects and company details can be shared outside Meta.",
            "Review generated bullets for accuracy and confidentiality before applying.",
        ],
    }

    output_path = PRIVATE_ROOT / "profile.yml"
    output_path.write_text(yaml.safe_dump(profile, sort_keys=False, allow_unicode=True), encoding="utf-8")
    click.echo(f"Wrote initial profile draft to {output_path}")


@main.command()
@click.argument("job_posting_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(exists=True, path_type=Path),
    default=PRIVATE_ROOT / "profile.yml",
    show_default=True,
    help="Structured private career profile to tailor from.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=OUTPUTS_ROOT,
    show_default=True,
    help="Directory where tailored artifacts will be written.",
)
@click.option(
    "--base-resume",
    type=click.Choice(["pm", "tpm"], case_sensitive=False),
    default=None,
    help="Use a private PM or TPM base resume when generating stronger tailored artifacts.",
)
@click.option(
    "--base-resume-path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Use a specific private base resume text or PDF file.",
)
def tailor_job(
    job_posting_path: Path,
    profile_path: Path,
    output_dir: Path,
    base_resume: str | None,
    base_resume_path: Path | None,
) -> None:
    """Generate a tailored resume draft and review notes for a job posting."""
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    job_text = job_posting_path.read_text(encoding="utf-8")
    job = _parse_job_posting(job_text, job_posting_path)
    alignment = _build_alignment(profile, job_text)
    evidence = _select_evidence(profile, job_text)
    gaps = _find_gaps(profile, job_text)

    job_slug = _slugify(job["title"] or job_posting_path.stem)
    job_output_dir = output_dir / job_slug
    job_output_dir.mkdir(parents=True, exist_ok=True)

    resume_path = job_output_dir / "resume_draft.md"
    notes_path = job_output_dir / "tailoring_notes.md"

    resume_path.write_text(
        _render_resume_draft(profile=profile, job=job, alignment=alignment, evidence=evidence),
        encoding="utf-8",
    )
    notes_path.write_text(
        _render_tailoring_notes(
            profile=profile,
            job=job,
            alignment=alignment,
            evidence=evidence,
            gaps=gaps,
            source=job_posting_path,
        ),
        encoding="utf-8",
    )

    if base_resume or base_resume_path:
        resolved_base_path = base_resume_path or _resolve_base_resume(base_resume or "")
        base_text = _load_resume_text(resolved_base_path)
        cleaned_base = _clean_resume_text(base_text)
        rewrite_plan_path = job_output_dir / "rewrite_plan.md"
        tailored_resume_path = job_output_dir / "resume_tailored.md"
        checklist_path = job_output_dir / "verification_checklist.md"

        rewrite_plan_path.write_text(
            _render_rewrite_plan(job=job, alignment=alignment, gaps=gaps, base_path=resolved_base_path),
            encoding="utf-8",
        )
        tailored_resume_path.write_text(
            _render_base_preserving_resume(
                profile=profile,
                job=job,
                alignment=alignment,
                base_resume_text=cleaned_base,
            ),
            encoding="utf-8",
        )
        checklist_path.write_text(
            _render_verification_checklist(profile=profile, job=job, gaps=gaps),
            encoding="utf-8",
        )
        click.echo(f"Wrote base-preserving tailored resume to {tailored_resume_path}")
        click.echo(f"Wrote rewrite plan to {rewrite_plan_path}")
        click.echo(f"Wrote verification checklist to {checklist_path}")

    click.echo(f"Wrote tailored resume draft to {resume_path}")
    click.echo(f"Wrote tailoring notes to {notes_path}")


@main.command()
@click.argument("job_posting_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(exists=True, path_type=Path),
    default=PRIVATE_ROOT / "profile.yml",
    show_default=True,
    help="Structured private career profile to match against.",
)
@click.option(
    "--base-resume",
    type=click.Choice(["pm", "tpm"], case_sensitive=False),
    default=None,
    help="Include a private PM or TPM base resume in match analysis.",
)
@click.option(
    "--base-resume-path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Include a specific private base resume text or PDF file in match analysis.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=OUTPUTS_ROOT,
    show_default=True,
    help="Directory where analysis artifacts will be written.",
)
def analyze_job(
    job_posting_path: Path,
    profile_path: Path,
    base_resume: str | None,
    base_resume_path: Path | None,
    output_dir: Path,
) -> None:
    """Analyze a job description and explain resume match quality."""
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    job_text = job_posting_path.read_text(encoding="utf-8")
    job = _parse_job_posting(job_text, job_posting_path)
    jd_analysis = _analyze_job_description(job_text, job)

    resume_text = ""
    resolved_base_path = None
    if base_resume or base_resume_path:
        resolved_base_path = base_resume_path or _resolve_base_resume(base_resume or "")
        resume_text = _clean_resume_text(_load_resume_text(resolved_base_path))

    match_report = _build_match_report(profile, resume_text, jd_analysis)

    job_slug = _slugify(str(job["title"]) or job_posting_path.stem)
    job_output_dir = output_dir / job_slug
    job_output_dir.mkdir(parents=True, exist_ok=True)

    jd_analysis_path = job_output_dir / "jd_analysis.yml"
    match_report_path = job_output_dir / "match_report.md"

    jd_analysis_path.write_text(
        yaml.safe_dump(jd_analysis, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    match_report_path.write_text(
        _render_match_report(
            job=job,
            jd_analysis=jd_analysis,
            match_report=match_report,
            source=job_posting_path,
            base_resume_path=resolved_base_path,
        ),
        encoding="utf-8",
    )

    click.echo(f"Wrote JD analysis to {jd_analysis_path}")
    click.echo(f"Wrote match report to {match_report_path}")


@main.command()
@click.argument("job_posting_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(exists=True, path_type=Path),
    default=PRIVATE_ROOT / "profile.yml",
    show_default=True,
    help="Structured private career profile to support truth checks.",
)
@click.option(
    "--base-resume",
    type=click.Choice(["pm", "tpm"], case_sensitive=False),
    default=None,
    help="Use a private PM or TPM base resume for side-by-side review.",
)
@click.option(
    "--base-resume-path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Use a specific private base resume text or PDF file.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=OUTPUTS_ROOT,
    show_default=True,
    help="Directory where review artifacts will be written.",
)
def review_diff(
    job_posting_path: Path,
    profile_path: Path,
    base_resume: str | None,
    base_resume_path: Path | None,
    output_dir: Path,
) -> None:
    """Generate side-by-side bullet rewrite suggestions for review."""
    if not base_resume and not base_resume_path:
        raise click.ClickException("Pass --base-resume or --base-resume-path for review-diff.")

    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    job_text = job_posting_path.read_text(encoding="utf-8")
    job = _parse_job_posting(job_text, job_posting_path)
    jd_analysis = _analyze_job_description(job_text, job)
    resolved_base_path = base_resume_path or _resolve_base_resume(base_resume or "")
    base_text = _clean_resume_text(_load_resume_text(resolved_base_path))
    suggestions = _build_bullet_review(profile, base_text, jd_analysis)

    job_slug = _slugify(str(job["title"]) or job_posting_path.stem)
    job_output_dir = output_dir / job_slug
    job_output_dir.mkdir(parents=True, exist_ok=True)

    review = {
        "job": {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "source": str(job_posting_path),
        },
        "base_resume": str(resolved_base_path),
        "review_items": suggestions,
    }

    review_yml_path = job_output_dir / "bullet_review.yml"
    review_md_path = job_output_dir / "bullet_review.md"
    review_yml_path.write_text(
        yaml.safe_dump(review, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    review_md_path.write_text(
        _render_bullet_review_markdown(review),
        encoding="utf-8",
    )

    click.echo(f"Wrote bullet review YAML to {review_yml_path}")
    click.echo(f"Wrote bullet review Markdown to {review_md_path}")


@main.command()
@click.argument("bullet_review_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory where approved artifacts will be written. Defaults to the review file directory.",
)
def apply_approved(bullet_review_path: Path, output_dir: Path | None) -> None:
    """Generate resume artifacts from approved or edited review items."""
    review = yaml.safe_load(bullet_review_path.read_text(encoding="utf-8")) or {}
    approved_items = _approved_review_items(review)
    target_dir = output_dir or bullet_review_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    resume_path = target_dir / "resume_approved.md"
    summary_path = target_dir / "approval_summary.md"

    resume_path.write_text(
        _render_approved_resume(review, approved_items),
        encoding="utf-8",
    )
    summary_path.write_text(
        _render_approval_summary(review, approved_items),
        encoding="utf-8",
    )

    click.echo(f"Wrote approved resume draft to {resume_path}")
    click.echo(f"Wrote approval summary to {summary_path}")


def _document_summary(relative_path: Path, text: str) -> dict[str, object]:
    return {
        "path": str(relative_path).replace("\\", "/"),
        "category": relative_path.parts[0] if relative_path.parts else "unknown",
        "characters": len(text),
        "likely_topics": _ranked_themes(text, limit=6),
    }


def _parse_job_posting(text: str, path: Path) -> dict[str, object]:
    lines = [line.strip(" #\t") for line in text.splitlines() if line.strip()]
    title = ""
    company = ""
    for line in lines[:12]:
        lower = line.lower()
        if not title and any(role in lower for role in ["manager", "program", "product", "lead"]):
            title = line
        if not company and lower.startswith("company:"):
            company = line.split(":", 1)[1].strip()
    return {
        "title": title or path.stem.replace("_", " ").replace("-", " ").title(),
        "company": company,
        "keywords": _job_keywords(text),
        "summary": _first_sentences(text, limit=5),
    }


def _analyze_job_description(text: str, job: dict[str, object]) -> dict[str, object]:
    bullets = _extract_bullets(text)
    lower = text.lower()
    return {
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "summary": job.get("summary", ""),
        "required_skills": _extract_requirements(text, bullets, required=True),
        "preferred_skills": _extract_requirements(text, bullets, required=False),
        "responsibilities": _extract_responsibilities(bullets),
        "tools": _matched_terms(lower, _TOOL_TERMS),
        "delivery_methods": _matched_terms(lower, _DELIVERY_METHOD_TERMS),
        "seniority_signals": _matched_terms(lower, _SENIORITY_SIGNAL_TERMS),
        "industry_keywords": _matched_terms(lower, _INDUSTRY_TERMS),
        "keywords": _job_keywords(text),
    }


def _build_match_report(
    profile: dict[str, object],
    resume_text: str,
    jd_analysis: dict[str, object],
) -> dict[str, object]:
    evidence_text = _profile_to_match_text(profile, resume_text)
    requirements = _requirements_for_scoring(jd_analysis)
    rows = []
    for requirement in requirements:
        support = _support_for_requirement(requirement, evidence_text)
        rows.append(
            {
                "requirement": requirement["text"],
                "category": requirement["category"],
                "confidence": support["confidence"],
                "evidence": support["evidence"],
                "explanation": support["explanation"],
                "weight": requirement["weight"],
            }
        )

    possible = sum(int(row["weight"]) for row in rows) or 1
    earned = sum(_confidence_points(str(row["confidence"])) * int(row["weight"]) for row in rows)
    score = round(earned / (possible * 3) * 100)

    return {
        "score": score,
        "strengths": [row for row in rows if row["confidence"] == "Strong"],
        "partial_matches": [row for row in rows if row["confidence"] == "Medium"],
        "missing_evidence": [row for row in rows if row["confidence"] in {"Needs Confirmation", "Missing"}],
        "scored_requirements": rows,
    }


def _build_bullet_review(
    profile: dict[str, object],
    base_resume_text: str,
    jd_analysis: dict[str, object],
    limit: int = 12,
) -> list[dict[str, object]]:
    bullets = _extract_resume_bullets(base_resume_text)
    requirements = _requirements_for_scoring(jd_analysis)
    evidence_text = _profile_to_match_text(profile, base_resume_text)
    review_items = []

    for bullet in bullets:
        best_requirement = _best_requirement_for_bullet(bullet, requirements)
        if not best_requirement:
            continue
        support = _support_for_requirement(best_requirement, evidence_text)
        suggested = _suggest_bullet_rewrite(bullet, best_requirement, jd_analysis)
        guardrail = _truthfulness_guardrail(
            original=bullet,
            suggested=suggested,
            evidence_text=evidence_text,
        )
        review_items.append(
            {
                "id": f"BR-{len(review_items) + 1:03d}",
                "original_bullet": bullet,
                "suggested_rewrite": suggested,
                "related_jd_requirement": best_requirement["text"],
                "requirement_category": best_requirement["category"],
                "reason_for_change": _reason_for_bullet_change(bullet, best_requirement),
                "supporting_evidence": support["evidence"],
                "confidence": support["confidence"],
                "truthfulness_risk": guardrail["truthfulness_risk"],
                "blocked_terms": guardrail["blocked_terms"],
                "confirmation_prompt": guardrail["confirmation_prompt"],
                "decision": "pending",
                "user_edit": "",
            }
        )
        if len(review_items) >= limit:
            break

    return review_items


def _extract_resume_bullets(text: str) -> list[str]:
    bullets = _extract_bullets(text)
    if bullets:
        return [bullet for bullet in bullets if len(bullet.split()) >= 6]

    inline_bullets = re.split(r"\s+-\s+", text)
    return [
        bullet.strip()
        for bullet in inline_bullets
        if len(bullet.split()) >= 6 and not bullet.strip().isupper()
    ]


def _best_requirement_for_bullet(
    bullet: str,
    requirements: list[dict[str, object]],
) -> dict[str, object] | None:
    scored = []
    for requirement in requirements:
        score = _token_overlap(str(requirement["text"]), bullet.lower())
        if score:
            scored.append((score * int(requirement["weight"]), requirement))
    if not scored:
        return None
    scored.sort(key=lambda item: -item[0])
    return scored[0][1]


def _suggest_bullet_rewrite(
    bullet: str,
    requirement: dict[str, object],
    jd_analysis: dict[str, object],
) -> str:
    bullet = _resume_bullet_from_claim(bullet)
    requirement_text = str(requirement["text"])
    category = str(requirement["category"])

    if category == "responsibilities":
        return f"{bullet[:-1]}, aligning delivery to {requirement_text[0].lower() + requirement_text[1:]}."
    if category in {"delivery_methods", "seniority_signals"}:
        return f"{bullet[:-1]}, reinforcing {requirement_text.lower()} expectations for the role."
    if category == "tools":
        return f"{bullet[:-1]}, with relevant experience connected to {requirement_text}."

    seniority = _comma_join(jd_analysis.get("seniority_signals", [])[:2])
    if seniority:
        return f"{bullet[:-1]}, emphasizing {seniority.lower()} in support of this role's requirements."
    return bullet


def _reason_for_bullet_change(bullet: str, requirement: dict[str, object]) -> str:
    return (
        "This bullet already has relevant evidence. The rewrite nudges wording toward "
        f"the JD requirement `{requirement['text']}` without adding unsupported facts."
    )


def _truthfulness_guardrail(
    original: str,
    suggested: str,
    evidence_text: str,
) -> dict[str, object]:
    original_lower = original.lower()
    suggested_lower = suggested.lower()
    introduced_terms = [
        term
        for term in _RISKY_CLAIM_TERMS
        if term in suggested_lower and term not in original_lower and term not in evidence_text
    ]
    introduced_metrics = _introduced_metric_claims(original_lower, suggested_lower)
    risky_verb_pairs = _introduced_verb_inflation(original_lower, suggested_lower)

    blocked_terms = _dedupe_preserve_order(
        [*introduced_terms, *introduced_metrics, *risky_verb_pairs]
    )

    if introduced_metrics or risky_verb_pairs:
        risk = "high"
    elif introduced_terms:
        risk = "medium"
    else:
        risk = "low"

    prompt = ""
    if risk == "high":
        prompt = (
            "Confirm this rewrite does not invent metrics, ownership, people management, "
            "certifications, tools, titles, or scope before approving."
        )
    elif risk == "medium":
        prompt = "Confirm the newly introduced scope/tool/seniority wording is directly supported."

    return {
        "truthfulness_risk": risk,
        "blocked_terms": blocked_terms,
        "confirmation_prompt": prompt,
    }


_RISKY_CLAIM_TERMS = [
    "managed engineers",
    "managed a team",
    "people manager",
    "owned p&l",
    "owned budget",
    "budget forecasting",
    "executive",
    "global",
    "enterprise",
    "multi-team",
    "director",
    "vp",
    "scrum master",
    "safe",
    "workday",
    "salesforce",
    "sap",
    "payroll",
    "hr systems",
    "finance systems",
]


_VERB_INFLATION_RULES = [
    (["partnered", "supported", "worked with", "contributed"], "managed"),
    (["supported", "contributed", "participated"], "owned"),
    (["helped", "supported", "participated"], "led"),
    (["partnered", "worked with"], "directed"),
]


def _introduced_metric_claims(original_lower: str, suggested_lower: str) -> list[str]:
    if _has_metric(suggested_lower) and not _has_metric(original_lower):
        return ["new metric claim"]
    metric_verbs = ["increased", "reduced", "saved", "improved by", "grew", "decreased"]
    return [
        verb
        for verb in metric_verbs
        if verb in suggested_lower and verb not in original_lower
    ]


def _has_metric(text: str) -> bool:
    return bool(re.search(r"(\$|\b\d+%|\b\d+x\b|\b\d+\s*(million|billion|k|m)\b)", text))


def _introduced_verb_inflation(original_lower: str, suggested_lower: str) -> list[str]:
    findings = []
    for weaker_verbs, stronger_verb in _VERB_INFLATION_RULES:
        if stronger_verb in suggested_lower and stronger_verb not in original_lower:
            if any(weak in original_lower for weak in weaker_verbs):
                findings.append(f"{', '.join(weaker_verbs)} -> {stronger_verb}")
    return findings


def _render_bullet_review_markdown(review: dict[str, object]) -> str:
    job = review.get("job", {})
    items = review.get("review_items", [])
    lines = [
        f"# Bullet Review: {job.get('title', 'Target Role')}",
        "",
        f"Company: {job.get('company') or 'Unknown'}",
        f"Source: `{job.get('source')}`",
        f"Base resume: `{review.get('base_resume')}`",
        "",
        "Review every item before using it in a resume. Decisions start as `pending`.",
        "",
    ]
    for item in items:
        lines.extend(
            [
                f"## {item['id']} - {item['confidence']}",
                "",
                "**Original bullet**",
                "",
                f"> {item['original_bullet']}",
                "",
                "**Suggested rewrite**",
                "",
                f"> {item['suggested_rewrite']}",
                "",
                f"Related JD requirement: {item['related_jd_requirement']}",
                f"Reason: {item['reason_for_change']}",
                f"Supporting evidence: {item['supporting_evidence'] or 'not found'}",
                f"Truthfulness risk: {item.get('truthfulness_risk', 'unknown')}",
                f"Blocked terms: {_comma_join(item.get('blocked_terms', [])) or 'none'}",
                f"Confirmation prompt: {item.get('confirmation_prompt') or 'none'}",
                f"Decision: {item['decision']}",
                "",
            ]
        )
    if not items:
        lines.extend(["No matching bullets found for review.", ""])
    return "\n".join(lines)


def _approved_review_items(review: dict[str, object]) -> list[dict[str, object]]:
    approved = []
    for item in review.get("review_items", []) or []:
        decision = str(item.get("decision", "pending")).lower()
        if decision == "approved":
            final_bullet = str(item.get("suggested_rewrite", "")).strip()
        elif decision == "edited":
            final_bullet = str(item.get("user_edit", "")).strip()
            if not final_bullet:
                continue
        else:
            continue

        approved.append(
            {
                **item,
                "decision": decision,
                "final_bullet": _resume_bullet_from_claim(final_bullet),
            }
        )
    return approved


def _render_approved_resume(
    review: dict[str, object],
    approved_items: list[dict[str, object]],
) -> str:
    job = review.get("job", {})
    lines = [
        f"# Reviewed Resume Bullets: {job.get('title', 'Target Role')}",
        "",
        "These bullets come only from review items marked `approved` or `edited`.",
        "",
        "## Approved Bullets",
        "",
    ]
    if approved_items:
        lines.extend(f"- {item['final_bullet']}" for item in approved_items)
    else:
        lines.append("- No approved or edited bullets found.")
    lines.extend(
        [
            "",
            "## Final Review",
            "",
            "- Confirm each approved bullet is true and safe to share.",
            "- Merge these bullets into the selected base resume format before applying.",
            "- Keep rejected and pending items out of the application resume.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_approval_summary(
    review: dict[str, object],
    approved_items: list[dict[str, object]],
) -> str:
    items = review.get("review_items", []) or []
    counts = {
        "approved": 0,
        "edited": 0,
        "rejected": 0,
        "pending": 0,
        "other": 0,
    }
    for item in items:
        decision = str(item.get("decision", "pending")).lower()
        if decision in counts:
            counts[decision] += 1
        else:
            counts["other"] += 1

    lines = [
        f"# Approval Summary: {(review.get('job') or {}).get('title', 'Target Role')}",
        "",
        f"- Approved: {counts['approved']}",
        f"- Edited: {counts['edited']}",
        f"- Rejected: {counts['rejected']}",
        f"- Pending: {counts['pending']}",
        f"- Other: {counts['other']}",
        f"- Included in approved resume: {len(approved_items)}",
        "",
        "## Included Items",
        "",
    ]
    if approved_items:
        lines.extend(
            f"- {item.get('id', 'item')}: {item['decision']} ({item.get('confidence', 'unknown')})"
            for item in approved_items
        )
    else:
        lines.append("- None.")
    lines.extend(["", "## Not Included", ""])
    excluded = [
        item
        for item in items
        if str(item.get("decision", "pending")).lower() not in {"approved", "edited"}
    ]
    if excluded:
        lines.extend(
            f"- {item.get('id', 'item')}: {item.get('decision', 'pending')}"
            for item in excluded
        )
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def _resolve_base_resume(base_resume: str) -> Path:
    normalized = base_resume.lower()
    label = "TPM" if normalized == "tpm" else "PM"
    candidates = [
        *sorted((EXTRACTED_ROOT / "resumes").glob(f"*{label}*.txt")),
        *sorted((SOURCE_ROOT / "resumes").glob(f"*{label}*.pdf")),
    ]
    if not candidates:
        raise click.ClickException(
            f"Could not find a private {label} resume. "
            "Run extract-sources or pass --base-resume-path."
        )
    return candidates[0]


def _load_resume_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8")


def _clean_resume_text(text: str) -> str:
    replacements = {
        "â€¢": "\n-",
        "•": "\n-",
        "Â°": "\n-",
        "\u00a0": " ",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"\n\s+", "\n", text)

    # PDF extraction often puts every word on its own line. Join short fragments while
    # preserving bullets and major resume sections.
    section_names = {
        "summary",
        "professional experience",
        "education & certifications",
        "technical toolkit",
    }
    joined_lines = []
    current = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                joined_lines.append(current.strip())
                current = ""
            joined_lines.append("")
            continue
        lower = line.lower()
        starts_new = (
            line.startswith("-")
            or lower in section_names
            or line.isupper()
            or re.search(r"\b(19|20)\d{2}\b", line)
        )
        if starts_new:
            if current:
                joined_lines.append(current.strip())
            current = line
        else:
            current = f"{current} {line}".strip()
    if current:
        joined_lines.append(current.strip())

    cleaned = "\n".join(joined_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _render_base_preserving_resume(
    profile: dict[str, object],
    job: dict[str, object],
    alignment: list[dict[str, object]],
    base_resume_text: str,
) -> str:
    name = profile.get("name", "Candidate")
    headline = (profile.get("positioning") or {}).get("headline", "")
    return "\n".join(
        [
            f"# {name}",
            "",
            f"## Targeted Resume For: {job.get('title', 'Target Role')}",
            "",
            "## Targeted Summary",
            "",
            _summary_for_job(str(headline), alignment),
            "",
            "## Priority Positioning",
            "",
            *[f"- {item['theme']}" for item in alignment[:8]],
            "",
            "## Base Resume Content To Preserve",
            "",
            base_resume_text,
            "",
            "## Final Editing Notes",
            "",
            "- Use this as a base-preserving rewrite, not a blank-slate generated resume.",
            "- Keep the original resume's strongest quantified bullets unless they are irrelevant or confidential.",
            "- Fold the targeted summary and priority positioning into the final resume format.",
            "",
        ]
    )


def _render_rewrite_plan(
    job: dict[str, object],
    alignment: list[dict[str, object]],
    gaps: list[str],
    base_path: Path,
) -> str:
    lines = [
        f"# Rewrite Plan: {job.get('title', 'Target Role')}",
        "",
        f"Base resume: `{base_path}`",
        "",
        "## Keep Strong",
        "",
        "- Preserve quantified impact, launch scope, cross-functional ownership, and recognizably senior TPM outcomes.",
        "- Preserve company chronology and the strongest bullets from the selected base resume.",
        "",
        "## Emphasize For This Role",
        "",
    ]
    lines.extend(f"- {item['theme']}" for item in alignment[:10])
    lines.extend(["", "## Be Careful With", ""])
    if gaps:
        lines.extend(f"- Do not overclaim `{gap}` unless the base resume or profile supports it." for gap in gaps)
    else:
        lines.append("- No major first-pass keyword gaps found.")
    lines.extend(
        [
            "",
            "## Editing Moves",
            "",
            "- Tune the summary to mirror the role's highest-value language.",
            "- Move the most relevant governance, risk, dependency, and executive-communication bullets higher.",
            "- Keep generated wording subordinate to verified source material.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_verification_checklist(
    profile: dict[str, object],
    job: dict[str, object],
    gaps: list[str],
) -> str:
    verification = profile.get("verification_needed") or []
    lines = [
        f"# Verification Checklist: {job.get('title', 'Target Role')}",
        "",
        "## Always Verify",
        "",
        "- Every metric and business impact claim.",
        "- Every certification, tool, platform, and methodology claim.",
        "- Every company-specific detail for confidentiality.",
        "- Final page length and formatting.",
        "",
        "## Profile Warnings",
        "",
    ]
    lines.extend(f"- {item}" for item in verification)
    lines.extend(["", "## Job-Specific Gaps To Confirm", ""])
    if gaps:
        lines.extend(f"- {gap}" for gap in gaps)
    else:
        lines.append("- No major first-pass gaps found.")
    lines.append("")
    return "\n".join(lines)


_TOOL_TERMS = [
    "Python",
    "SQL",
    "Tableau",
    "Looker",
    "AWS",
    "Snowflake",
    "Kafka",
    "Spark",
    "Airflow",
    "Salesforce",
    "Workday",
    "Oracle",
    "SAP",
    "Jira",
    "Confluence",
    "Figma",
    "LLM",
    "AI",
    "ML",
]

_DELIVERY_METHOD_TERMS = [
    "Agile",
    "Scrum",
    "Kanban",
    "SAFe",
    "PI Planning",
    "Waterfall",
    "hybrid delivery",
    "roadmap",
    "governance",
    "risk management",
    "dependency management",
    "retrospective",
]

_SENIORITY_SIGNAL_TERMS = [
    "senior",
    "executive",
    "leadership",
    "stakeholder",
    "cross-functional",
    "matrixed",
    "strategy",
    "portfolio",
    "budget",
    "forecasting",
    "governance",
]

_INDUSTRY_TERMS = [
    "AI",
    "machine learning",
    "ads",
    "platform",
    "developer tools",
    "finance",
    "payroll",
    "HR",
    "employee success",
    "data",
    "infrastructure",
    "identity",
    "biometrics",
]


def _extract_bullets(text: str) -> list[str]:
    bullets = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned.startswith(("-", "*", "•")):
            bullets.append(cleaned.lstrip("-*• ").strip())
    return bullets


def _extract_requirements(text: str, bullets: list[str], required: bool) -> list[str]:
    lower_markers = (
        ["required", "qualification", "must", "minimum"] if required else ["preferred", "nice", "bonus"]
    )
    selected = []
    current_section_matches = False
    for line in text.splitlines():
        cleaned = line.strip(" #\t-*•")
        if not cleaned:
            continue
        lower = cleaned.lower()
        if any(marker in lower for marker in lower_markers):
            current_section_matches = True
            if len(cleaned.split()) > 3 and not lower.endswith("qualifications"):
                selected.append(cleaned)
            continue
        if re.match(r"^[A-Z][A-Za-z &/-]{2,}:?$", cleaned) and not cleaned.startswith("-"):
            current_section_matches = False
        elif current_section_matches and line.strip().startswith(("-", "*", "•")):
            selected.append(cleaned)

    if not selected and required:
        selected = [
            bullet
            for bullet in bullets
            if any(word in bullet.lower() for word in ["experience", "ability", "knowledge", "lead"])
        ]

    return _dedupe_preserve_order(selected)[:12]


def _extract_responsibilities(bullets: list[str]) -> list[str]:
    action_words = [
        "lead",
        "partner",
        "drive",
        "define",
        "manage",
        "identify",
        "facilitate",
        "produce",
        "coordinate",
        "support",
        "create",
        "own",
    ]
    responsibilities = [
        bullet
        for bullet in bullets
        if any(bullet.lower().startswith(word) for word in action_words)
    ]
    return _dedupe_preserve_order(responsibilities)[:14]


def _matched_terms(lower_text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term.lower() in lower_text]


def _requirements_for_scoring(jd_analysis: dict[str, object]) -> list[dict[str, object]]:
    weighted_sections = [
        ("required_skills", 3),
        ("responsibilities", 2),
        ("tools", 2),
        ("delivery_methods", 2),
        ("seniority_signals", 1),
        ("industry_keywords", 1),
        ("preferred_skills", 1),
    ]
    requirements = []
    seen = set()
    for category, weight in weighted_sections:
        for value in jd_analysis.get(category, []) or []:
            text = str(value).strip()
            key = text.lower()
            if text and key not in seen:
                seen.add(key)
                requirements.append({"category": category, "text": text, "weight": weight})
    return requirements[:50]


def _profile_to_match_text(profile: dict[str, object], resume_text: str) -> str:
    profile_parts = [
        str(profile.get("target_roles", "")),
        str(profile.get("positioning", "")),
        str(profile.get("skills", "")),
        str(profile.get("feedback_themes", "")),
        str(profile.get("evidence_snippets", "")),
    ]
    return "\n".join([*profile_parts, resume_text]).lower()


def _support_for_requirement(requirement: dict[str, object], evidence_text: str) -> dict[str, str]:
    requirement_text = str(requirement["text"])
    tokens = _important_tokens(requirement_text)
    hits = [token for token in tokens if token in evidence_text]

    if requirement_text.lower() in evidence_text or len(hits) >= 3:
        confidence = "Strong"
        explanation = "Direct wording or multiple important terms appear in the resume/profile evidence."
    elif len(hits) >= 2:
        confidence = "Medium"
        explanation = "Related terms appear, but the exact requirement should be verified before using stronger wording."
    elif len(hits) == 1:
        confidence = "Needs Confirmation"
        explanation = "Only a weak signal appears; a rewrite should ask the user to confirm before claiming this."
    else:
        confidence = "Missing"
        explanation = "No clear supporting evidence found in the available resume/profile text."

    return {
        "confidence": confidence,
        "evidence": ", ".join(hits[:8]) if hits else "",
        "explanation": explanation,
    }


def _important_tokens(text: str) -> list[str]:
    stop_words = {
        "ability",
        "across",
        "also",
        "and",
        "are",
        "deliver",
        "experience",
        "for",
        "from",
        "have",
        "including",
        "lead",
        "manage",
        "must",
        "our",
        "such",
        "that",
        "the",
        "this",
        "using",
        "with",
        "years",
        "your",
    }
    tokens = re.findall(r"[A-Za-z][A-Za-z+/.-]{2,}", text.lower())
    return _dedupe_preserve_order([token for token in tokens if token not in stop_words and len(token) > 3])


def _confidence_points(confidence: str) -> int:
    return {
        "Strong": 3,
        "Medium": 2,
        "Needs Confirmation": 1,
        "Missing": 0,
    }.get(confidence, 0)


def _render_match_report(
    job: dict[str, object],
    jd_analysis: dict[str, object],
    match_report: dict[str, object],
    source: Path,
    base_resume_path: Path | None,
) -> str:
    lines = [
        f"# Match Report: {job.get('title', source.stem)}",
        "",
        f"Source posting: `{source}`",
        f"Base resume: `{base_resume_path}`" if base_resume_path else "Base resume: not provided",
        "",
        f"## Match Score: {match_report['score']}%",
        "",
        "The score is explainable and evidence-based. It is not a promise of interview success.",
        "",
        "## JD Analyzer Summary",
        "",
        f"- Required skills: {len(jd_analysis.get('required_skills', []))}",
        f"- Preferred skills: {len(jd_analysis.get('preferred_skills', []))}",
        f"- Responsibilities: {len(jd_analysis.get('responsibilities', []))}",
        f"- Tools/platforms: {_comma_join(jd_analysis.get('tools', [])) or 'None detected'}",
        f"- Delivery methods: {_comma_join(jd_analysis.get('delivery_methods', [])) or 'None detected'}",
        f"- Seniority signals: {_comma_join(jd_analysis.get('seniority_signals', [])) or 'None detected'}",
        "",
        "## Strengths",
        "",
    ]
    lines.extend(_render_match_rows(match_report.get("strengths", [])))
    lines.extend(["", "## Partial Matches", ""])
    lines.extend(_render_match_rows(match_report.get("partial_matches", [])))
    lines.extend(["", "## Missing Or Needs Confirmation", ""])
    lines.extend(_render_match_rows(match_report.get("missing_evidence", [])))
    lines.extend(
        [
            "",
            "## How To Use This",
            "",
            "- Use Strong matches as safe tailoring themes.",
            "- Treat Medium matches as wording candidates that need careful phrasing.",
            "- Treat Needs Confirmation or Missing items as prompts for user confirmation, not resume claims.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_match_rows(rows: list[dict[str, object]]) -> list[str]:
    if not rows:
        return ["- None found."]
    return [
        (
            f"- **{row['confidence']}** `{row['category']}`: {row['requirement']} "
            f"Evidence: {row['evidence'] or 'not found'}. {row['explanation']}"
        )
        for row in rows[:20]
    ]


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    deduped = []
    seen = set()
    for value in values:
        key = value.lower().strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(value.strip())
    return deduped


def _build_alignment(profile: dict[str, object], job_text: str) -> list[dict[str, object]]:
    profile_items = []
    positioning = profile.get("positioning") or {}
    if isinstance(positioning, dict):
        profile_items.extend(positioning.get("themes") or [])
    profile_items.extend(profile.get("skills") or [])
    profile_items.extend(profile.get("feedback_themes") or [])

    lower_job = job_text.lower()
    aligned = []
    for item in profile_items:
        score = _token_overlap(str(item), lower_job)
        if score:
            aligned.append({"theme": str(item), "score": score})

    aligned.sort(key=lambda row: (-int(row["score"]), str(row["theme"])))
    return aligned[:10]


def _select_evidence(profile: dict[str, object], job_text: str, limit: int = 8) -> list[dict[str, object]]:
    snippets = profile.get("evidence_snippets") or []
    lower_job = job_text.lower()
    ranked = []
    for snippet in snippets:
        claim = str(snippet.get("claim", "")) if isinstance(snippet, dict) else str(snippet)
        score = _token_overlap(claim, lower_job)
        if score:
            ranked.append({"claim": claim, "score": score, "status": "needs_review"})

    if not ranked:
        for snippet in snippets[:limit]:
            claim = str(snippet.get("claim", "")) if isinstance(snippet, dict) else str(snippet)
            ranked.append({"claim": claim, "score": 0, "status": "needs_review"})

    ranked.sort(key=lambda row: (-int(row["score"]), str(row["claim"])))
    return ranked[:limit]


def _find_gaps(profile: dict[str, object], job_text: str) -> list[str]:
    profile_text = " ".join(
        str(value)
        for key, value in profile.items()
        if key not in {"documents", "evidence_snippets", "verification_needed"}
    ).lower()
    gaps = []
    for keyword in _job_keywords(job_text):
        if keyword.lower() not in profile_text and len(gaps) < 8:
            gaps.append(keyword)
    return gaps


def _render_resume_draft(
    profile: dict[str, object],
    job: dict[str, object],
    alignment: list[dict[str, object]],
    evidence: list[dict[str, object]],
) -> str:
    name = profile.get("name", "Candidate")
    headline = (profile.get("positioning") or {}).get("headline", "")
    skills = profile.get("skills") or []
    target_title = job.get("title", "Target Role")

    bullets = [
        _resume_bullet_from_claim(str(item["claim"]))
        for item in evidence
        if str(item.get("claim", "")).strip()
    ]

    return "\n".join(
        [
            f"# {name}",
            "",
            f"## Target Role: {target_title}",
            "",
            "## Summary",
            "",
            _summary_for_job(str(headline), alignment),
            "",
            "## Selected Skills",
            "",
            _comma_join(skills[:14]),
            "",
            "## Experience Highlights",
            "",
            *[f"- {bullet}" for bullet in bullets],
            "",
            "## Review Before Use",
            "",
            "- Replace this draft structure with your preferred resume format.",
            "- Verify every metric, claim, and company-specific detail before applying.",
            "- Remove anything confidential or too Meta-internal for an external application.",
            "",
        ]
    )


def _render_tailoring_notes(
    profile: dict[str, object],
    job: dict[str, object],
    alignment: list[dict[str, object]],
    evidence: list[dict[str, object]],
    gaps: list[str],
    source: Path,
) -> str:
    verification = profile.get("verification_needed") or []
    lines = [
        f"# Tailoring Notes: {job.get('title', source.stem)}",
        "",
        f"Source posting: `{source}`",
        "",
        "## Strongest Alignment",
        "",
    ]
    lines.extend(f"- {item['theme']} (score: {item['score']})" for item in alignment)
    lines.extend(["", "## Evidence To Consider", ""])
    lines.extend(f"- {item['claim']} [review]" for item in evidence)
    lines.extend(["", "## Possible Gaps", ""])
    if gaps:
        lines.extend(f"- {gap}" for gap in gaps)
    else:
        lines.append("- No obvious keyword gaps found in this first-pass scan.")
    lines.extend(["", "## Verification Checklist", ""])
    lines.extend(f"- {item}" for item in verification)
    lines.extend(
        [
            "- Confirm selected bullets directly answer the job's responsibilities.",
            "- Confirm the final resume stays within the requested page length.",
            "",
        ]
    )
    return "\n".join(lines)


def _summary_for_job(headline: str, alignment: list[dict[str, object]]) -> str:
    top_themes = [str(item["theme"]) for item in alignment[:3]]
    if not top_themes:
        return headline
    return f"{headline} Strongest fit signals for this role: {_comma_join(top_themes)}."


def _resume_bullet_from_claim(claim: str) -> str:
    claim = claim.strip().rstrip(".")
    if not claim:
        return ""
    if claim[:1].isupper():
        return claim + "."
    return claim[:1].upper() + claim[1:] + "."


def _job_keywords(text: str, limit: int = 24) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z+/.-]{2,}", text.lower())
    stop_words = {
        "and",
        "are",
        "for",
        "from",
        "have",
        "our",
        "that",
        "the",
        "this",
        "with",
        "you",
        "your",
        "will",
    }
    counts = {}
    for word in words:
        if word in stop_words or len(word) < 4:
            continue
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ranked[:limit]]


def _token_overlap(source_text: str, lower_target_text: str) -> int:
    tokens = {
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z+/.-]{3,}", source_text)
        if token.lower() not in {"and", "with", "from", "that", "this"}
    }
    return sum(1 for token in tokens if token in lower_target_text)


def _first_sentences(text: str, limit: int = 5) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", compact)
    return " ".join(sentences[:limit])


def _comma_join(items: list[object]) -> str:
    return ", ".join(str(item) for item in items if str(item).strip())


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "job"


def _first_match(text: str, pattern: str, default: str = "") -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else default


def _best_headline(text: str) -> str:
    if "Technical Program Manager" in text and "Product Manager" in text:
        return "AI product and technical program leader across ML ads delivery, ranking, optimization, and large-scale launches."
    if "Technical Program Manager" in text:
        return "Technical program leader for ambiguous, cross-functional platform and AI delivery work."
    return "Product leader for AI, ranking, optimization, and cross-functional product execution."


def _ranked_themes(text: str, limit: int = 10) -> list[str]:
    candidates = {
        "AI and machine learning product strategy": ["AI", "ML", "machine learning", "model"],
        "Ads delivery, ranking, and optimization": ["ads", "ranking", "optimization", "auction"],
        "Large-scale cross-functional execution": ["cross-functional", "launch", "roadmap", "execution"],
        "Platform and infrastructure programs": ["platform", "infrastructure", "systems", "workflow"],
        "Stakeholder alignment and executive communication": ["stakeholder", "executive", "alignment", "communication"],
        "Metrics, experimentation, and impact measurement": ["metrics", "experiment", "measurement", "impact"],
        "Ambiguity, strategy, and operating cadence": ["ambiguous", "strategy", "cadence", "planning"],
        "Privacy, compliance, and responsible delivery": ["privacy", "compliance", "risk", "guardrail"],
        "Operational rigor and process improvement": ["process", "operations", "operational", "efficiency"],
        "Team leadership and coaching": ["mentor", "coach", "leadership", "team"],
    }
    return _rank_candidates(text, candidates, limit)


def _ranked_skills(text: str, limit: int = 18) -> list[str]:
    candidates = {
        "Product strategy": ["product strategy", "strategy"],
        "Technical program management": ["technical program", "TPM"],
        "AI/ML systems": ["AI", "ML", "machine learning"],
        "Ads ranking": ["ranking"],
        "Optimization": ["optimization"],
        "Roadmapping": ["roadmap"],
        "Launch management": ["launch"],
        "Experimentation": ["experiment"],
        "Metrics definition": ["metrics"],
        "Stakeholder management": ["stakeholder"],
        "Executive communication": ["executive"],
        "Cross-functional leadership": ["cross-functional"],
        "Risk management": ["risk"],
        "Privacy review": ["privacy"],
        "Platform products": ["platform"],
        "Process improvement": ["process"],
        "Data-informed decision making": ["data"],
        "Product operations": ["operations"],
    }
    return _rank_candidates(text, candidates, limit)


def _feedback_themes(text: str) -> list[str]:
    candidates = {
        "Creates structure in ambiguous work": ["ambiguous", "clarity", "structure"],
        "Strong cross-functional partner": ["cross-functional", "partner", "stakeholder"],
        "Communicates clearly": ["communication", "communicator", "clear"],
        "Drives execution and follow-through": ["execution", "follow-through", "delivery"],
        "Builds trust with teams": ["trust", "relationship", "collaboration"],
        "Improves processes": ["process", "efficiency", "operating"],
    }
    return _rank_candidates(text, candidates, 8)


def _evidence_snippets(text: str, limit: int = 30) -> list[dict[str, str]]:
    cleaned_lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < 45 or len(line) > 240:
            continue
        if _looks_like_evidence(line):
            cleaned_lines.append(line)

    deduped = []
    seen = set()
    for line in cleaned_lines:
        key = line.lower()
        if key not in seen:
            seen.add(key)
            deduped.append({"claim": line, "status": "needs_review"})
        if len(deduped) >= limit:
            break
    return deduped


def _looks_like_evidence(line: str) -> bool:
    evidence_words = [
        "led",
        "launched",
        "built",
        "improved",
        "reduced",
        "increased",
        "drove",
        "managed",
        "partnered",
        "delivered",
        "defined",
        "created",
        "scaled",
        "saved",
        "%",
        "$",
    ]
    lower = line.lower()
    return any(word in lower for word in evidence_words)


def _rank_candidates(text: str, candidates: dict[str, list[str]], limit: int) -> list[str]:
    lower = text.lower()
    scored = []
    for label, keywords in candidates.items():
        score = sum(lower.count(keyword.lower()) for keyword in keywords)
        if score:
            scored.append((score, label))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [label for _, label in scored[:limit]]


if __name__ == "__main__":
    main()
