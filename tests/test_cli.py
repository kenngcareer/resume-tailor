from click.testing import CliRunner

from resume_tailor.cli import main


def test_cli_help() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Resume tailoring workflow commands" in result.output
    assert "tailor-job" in result.output
    assert "analyze-job" in result.output


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
