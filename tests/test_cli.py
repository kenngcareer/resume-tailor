from click.testing import CliRunner

from resume_tailor.cli import _contains_any, _extract_resume_bullets, _truthfulness_guardrail, main


def test_cli_help() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Resume tailoring workflow commands" in result.output
    assert "tailor-job" in result.output
    assert "analyze-job" in result.output
    assert "review-diff" in result.output
    assert "apply-approved" in result.output
    assert "export-docx" in result.output
    assert "demo" in result.output


def test_tailor_job_writes_outputs(tmp_path) -> None:
    profile_path = tmp_path / "profile.yml"
    job_path = tmp_path / "job.md"
    output_dir = tmp_path / "outputs"

    profile_path.write_text(
        """
name: Example Candidate
target_roles:
  - Product Manager
positioning:
  headline: AI product leader for platform execution.
  themes:
    - AI and machine learning product strategy
skills:
  - Product strategy
  - Cross-functional leadership
evidence_snippets:
  - claim: Led cross-functional AI platform launch across product and engineering teams.
    status: needs_review
feedback_themes:
  - Communicates clearly
verification_needed:
  - Confirm metrics.
""".strip(),
        encoding="utf-8",
    )
    job_path.write_text(
        "Senior Product Manager\nLead AI platform strategy and cross-functional launches.",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        [
            "tailor-job",
            str(job_path),
            "--profile",
            str(profile_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert (output_dir / "senior-product-manager" / "resume_draft.md").exists()
    assert (output_dir / "senior-product-manager" / "tailoring_notes.md").exists()


def test_tailor_job_with_base_resume_writes_stronger_outputs(tmp_path) -> None:
    profile_path = tmp_path / "profile.yml"
    job_path = tmp_path / "job.md"
    base_resume_path = tmp_path / "base_resume.txt"
    output_dir = tmp_path / "outputs"

    profile_path.write_text(
        """
name: Example Candidate
target_roles:
  - Technical Program Manager
positioning:
  headline: Enterprise TPM for AI platform delivery.
  themes:
    - Large-scale cross-functional execution
    - Stakeholder alignment and executive communication
skills:
  - Technical program management
  - Risk management
evidence_snippets:
  - claim: Led executive governance for an AI platform launch.
    status: needs_review
feedback_themes:
  - Communicates clearly
verification_needed:
  - Confirm certifications.
""".strip(),
        encoding="utf-8",
    )
    job_path.write_text(
        "Senior Technical Program Manager\nLead governance, risk, and executive communication.",
        encoding="utf-8",
    )
    base_resume_path.write_text(
        "EXAMPLE CANDIDATE\nSUMMARY\nEnterprise TPM.\nPROFESSIONAL EXPERIENCE\n- Led launch governance with measurable impact.",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        [
            "tailor-job",
            str(job_path),
            "--profile",
            str(profile_path),
            "--base-resume-path",
            str(base_resume_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    target_dir = output_dir / "senior-technical-program-manager"
    assert result.exit_code == 0
    assert (target_dir / "resume_tailored.md").exists()
    assert (target_dir / "rewrite_plan.md").exists()
    assert (target_dir / "verification_checklist.md").exists()
    assert "Base Resume Content To Preserve" in (target_dir / "resume_tailored.md").read_text(
        encoding="utf-8"
    )


def test_analyze_job_writes_jd_analysis_and_match_report(tmp_path) -> None:
    profile_path = tmp_path / "profile.yml"
    job_path = tmp_path / "job.md"
    base_resume_path = tmp_path / "base_resume.txt"
    output_dir = tmp_path / "outputs"

    profile_path.write_text(
        """
name: Example Candidate
target_roles:
  - Technical Program Manager
positioning:
  headline: TPM for enterprise AI programs.
  themes:
    - Executive communication
    - Risk management
skills:
  - Agile
  - SQL
  - Stakeholder management
evidence_snippets:
  - claim: Led executive governance and risk tracking for an enterprise AI platform.
    status: needs_review
verification_needed:
  - Confirm certifications.
""".strip(),
        encoding="utf-8",
    )
    job_path.write_text(
        """
# Senior Technical Program Manager

## Required Qualifications

- 7+ years technical program management experience.
- Ability to lead executive communication and risk management.
- Experience with Agile delivery and SQL.

## Responsibilities

- Lead cross-functional roadmap planning.
- Produce governance readouts and decision logs.
""".strip(),
        encoding="utf-8",
    )
    base_resume_path.write_text(
        "Led executive governance, Agile delivery, SQL reporting, and risk tracking.",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        [
            "analyze-job",
            str(job_path),
            "--profile",
            str(profile_path),
            "--base-resume-path",
            str(base_resume_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    target_dir = output_dir / "senior-technical-program-manager"
    assert result.exit_code == 0
    assert (target_dir / "jd_analysis.yml").exists()
    assert (target_dir / "match_report.md").exists()
    report = (target_dir / "match_report.md").read_text(encoding="utf-8")
    assert "Match Score" in report
    assert "Strengths" in report
    assert "Missing Or Needs Confirmation" in report


def test_review_diff_writes_side_by_side_review(tmp_path) -> None:
    profile_path = tmp_path / "profile.yml"
    job_path = tmp_path / "job.md"
    base_resume_path = tmp_path / "base_resume.txt"
    output_dir = tmp_path / "outputs"

    profile_path.write_text(
        """
name: Example Candidate
positioning:
  headline: Enterprise TPM.
  themes:
    - Risk management
skills:
  - Agile
  - executive communication
evidence_snippets:
  - claim: Led executive governance, Agile delivery, and risk management.
    status: needs_review
""".strip(),
        encoding="utf-8",
    )
    job_path.write_text(
        """
# Senior Technical Program Manager

## Required Qualifications

- Ability to lead executive communication and risk management.

## Responsibilities

- Lead cross-functional roadmap planning.
""".strip(),
        encoding="utf-8",
    )
    base_resume_path.write_text(
        """
EXAMPLE CANDIDATE
PROFESSIONAL EXPERIENCE
- Led executive governance, Agile delivery, and risk management for a platform launch.
- Improved support readiness and decision logs across stakeholders.
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        [
            "review-diff",
            str(job_path),
            "--profile",
            str(profile_path),
            "--base-resume-path",
            str(base_resume_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    target_dir = output_dir / "senior-technical-program-manager"
    assert result.exit_code == 0
    assert (target_dir / "bullet_review.yml").exists()
    assert (target_dir / "bullet_review.md").exists()
    review = (target_dir / "bullet_review.md").read_text(encoding="utf-8")
    assert "Original bullet" in review
    assert "Suggested rewrite" in review
    assert "Truthfulness risk" in review
    assert "Decision: pending" in review
    assert "aligning delivery to" not in review
    assert "reinforcing" not in review


def test_resume_bullet_extraction_skips_skill_inventory() -> None:
    bullets = _extract_resume_bullets(
        """
- ML ads delivery: ranking, calibration, auction mechanics, attribution, pricing, quality
- Led cross-functional launch governance and risk tracking for a platform rollout.
- Product strategy: roadmap planning, prioritization, launch metrics
""".strip()
    )

    assert bullets == [
        "Led cross-functional launch governance and risk tracking for a platform rollout."
    ]


def test_resume_bullet_extraction_joins_continuations() -> None:
    bullets = _extract_resume_bullets(
        """
- Led launch from alpha to GA and generated
>$100M in revenue across markets.
- Product strategy: roadmap planning, prioritization, launch metrics
""".strip()
    )

    assert bullets == ["Led launch from alpha to GA and generated >$100M in revenue across markets."]


def test_contains_any_uses_term_boundaries() -> None:
    assert not _contains_any("exceeded ads-value gain goal", ["ga"])
    assert _contains_any("scaled through GA rollout", ["ga"])


def test_apply_approved_uses_only_approved_and_edited_items(tmp_path) -> None:
    review_path = tmp_path / "bullet_review.yml"
    output_dir = tmp_path / "approved"

    review_path.write_text(
        """
job:
  title: Senior Technical Program Manager
  company: ExampleCo
base_resume: base_resume.txt
review_items:
  - id: BR-001
    original_bullet: Original one.
    suggested_rewrite: Approved rewrite for governance.
    confidence: Strong
    decision: approved
    user_edit: ''
  - id: BR-002
    original_bullet: Original two.
    suggested_rewrite: Suggested rewrite should not be used.
    confidence: Medium
    decision: edited
    user_edit: Edited rewrite for risk management.
  - id: BR-003
    original_bullet: Original three.
    suggested_rewrite: Rejected rewrite.
    confidence: Strong
    decision: rejected
    user_edit: ''
  - id: BR-004
    original_bullet: Original four.
    suggested_rewrite: Pending rewrite.
    confidence: Needs Confirmation
    decision: pending
    user_edit: ''
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        [
            "apply-approved",
            str(review_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    resume = (output_dir / "resume_approved.md").read_text(encoding="utf-8")
    reconstructed = (output_dir / "resume_reconstructed.md").read_text(encoding="utf-8")
    summary = (output_dir / "approval_summary.md").read_text(encoding="utf-8")
    blocked = (output_dir / "blocked_items.md").read_text(encoding="utf-8")
    assert "Approved rewrite for governance" in resume
    assert "Edited rewrite for risk management" in resume
    assert "Rejected rewrite" not in resume
    assert "Pending rewrite" not in resume
    assert "Targeted Summary" in reconstructed
    assert "Experience Highlights" in reconstructed
    assert "Edited rewrite for risk management" in reconstructed
    assert "Included in approved resume: 2" in summary
    assert "Reconstructed resume" in summary
    assert "No items were blocked" in blocked


def test_apply_approved_blocks_medium_without_confirmation(tmp_path) -> None:
    review_path = tmp_path / "bullet_review.yml"
    output_dir = tmp_path / "approved"

    review_path.write_text(
        """
job:
  title: Senior Technical Program Manager
review_items:
  - id: BR-001
    original_bullet: Led delivery governance.
    suggested_rewrite: Led Salesforce delivery governance.
    confidence: Medium
    truthfulness_risk: medium
    blocked_terms:
      - salesforce
    decision: approved
    user_edit: ''
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["apply-approved", str(review_path), "--output-dir", str(output_dir)],
    )

    assert result.exit_code == 0
    resume = (output_dir / "resume_approved.md").read_text(encoding="utf-8")
    summary = (output_dir / "approval_summary.md").read_text(encoding="utf-8")
    blocked = (output_dir / "blocked_items.md").read_text(encoding="utf-8")
    assert "Led Salesforce delivery governance" not in resume
    assert "Blocked by truthfulness guardrail: 1" in summary
    assert "requires confirmation_note" in blocked


def test_apply_approved_allows_medium_with_confirmation(tmp_path) -> None:
    review_path = tmp_path / "bullet_review.yml"
    output_dir = tmp_path / "approved"

    review_path.write_text(
        """
job:
  title: Senior Technical Program Manager
review_items:
  - id: BR-001
    original_bullet: Led delivery governance.
    suggested_rewrite: Led Salesforce delivery governance.
    confidence: Medium
    truthfulness_risk: medium
    blocked_terms:
      - salesforce
    confirmation_note: Confirmed Salesforce experience is accurate.
    decision: approved
    user_edit: ''
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["apply-approved", str(review_path), "--output-dir", str(output_dir)],
    )

    resume = (output_dir / "resume_approved.md").read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "Led Salesforce delivery governance" in resume


def test_apply_approved_blocks_high_without_override(tmp_path) -> None:
    review_path = tmp_path / "bullet_review.yml"
    output_dir = tmp_path / "approved"

    review_path.write_text(
        """
job:
  title: Senior Technical Program Manager
review_items:
  - id: BR-001
    original_bullet: Partnered with engineering teams.
    suggested_rewrite: Managed engineering teams.
    confidence: Needs Confirmation
    truthfulness_risk: high
    blocked_terms:
      - partnered -> managed
    confirmation_note: Confirmed direct management.
    decision: approved
    user_edit: ''
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["apply-approved", str(review_path), "--output-dir", str(output_dir)],
    )

    resume = (output_dir / "resume_approved.md").read_text(encoding="utf-8")
    blocked = (output_dir / "blocked_items.md").read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "Managed engineering teams" not in resume
    assert "requires override_truthfulness_block" in blocked


def test_apply_approved_allows_high_with_override(tmp_path) -> None:
    review_path = tmp_path / "bullet_review.yml"
    output_dir = tmp_path / "approved"

    review_path.write_text(
        """
job:
  title: Senior Technical Program Manager
review_items:
  - id: BR-001
    original_bullet: Partnered with engineering teams.
    suggested_rewrite: Managed engineering teams.
    confidence: Needs Confirmation
    truthfulness_risk: high
    blocked_terms:
      - partnered -> managed
    confirmation_note: Confirmed direct management.
    override_truthfulness_block: true
    decision: approved
    user_edit: ''
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["apply-approved", str(review_path), "--output-dir", str(output_dir)],
    )

    resume = (output_dir / "resume_approved.md").read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "Managed engineering teams" in resume


def test_export_docx_writes_docx_and_summary(tmp_path) -> None:
    markdown_path = tmp_path / "resume_approved.md"
    docx_path = tmp_path / "resume_approved.docx"

    markdown_path.write_text(
        """
# Example Candidate

## Summary

Enterprise TPM with AI platform experience.

## Approved Bullets

- Led governance for a platform launch.
- Improved risk tracking across stakeholders.
""".strip(),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["export-docx", str(markdown_path), "--output-path", str(docx_path)],
    )

    assert result.exit_code == 0
    assert docx_path.exists()
    assert docx_path.stat().st_size > 0
    summary = (tmp_path / "resume_approved_export_summary.md").read_text(encoding="utf-8")
    assert "single column" in summary
    assert "no tables" in summary


def test_demo_writes_public_demo_artifacts(tmp_path) -> None:
    result = CliRunner().invoke(main, ["demo", "--output-dir", str(tmp_path)])

    target_dir = tmp_path / "senior-technical-program-manager"
    assert result.exit_code == 0
    assert (target_dir / "jd_analysis.yml").exists()
    assert (target_dir / "match_report.md").exists()
    assert (target_dir / "bullet_review.yml").exists()
    assert (target_dir / "resume_approved.md").exists()
    assert (target_dir / "resume_reconstructed.md").exists()
    assert (target_dir / "resume_approved.docx").exists()


def test_truthfulness_guardrail_flags_risky_verb_inflation() -> None:
    guardrail = _truthfulness_guardrail(
        original="Partnered with engineering teams on rollout planning.",
        suggested="Managed engineering teams on rollout planning.",
        evidence_text="partnered with engineering teams on rollout planning.",
    )

    assert guardrail["truthfulness_risk"] == "high"
    assert "partnered, supported, worked with, contributed -> managed" in guardrail["blocked_terms"]
    assert "Confirm" in guardrail["confirmation_prompt"]


def test_truthfulness_guardrail_flags_unsupported_tool_claim() -> None:
    guardrail = _truthfulness_guardrail(
        original="Led delivery governance for a platform launch.",
        suggested="Led Salesforce delivery governance for a global platform launch.",
        evidence_text="led delivery governance for a platform launch.",
    )

    assert guardrail["truthfulness_risk"] == "medium"
    assert "salesforce" in guardrail["blocked_terms"]
    assert "global" in guardrail["blocked_terms"]
