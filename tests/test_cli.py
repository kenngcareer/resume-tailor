from click.testing import CliRunner

from resume_tailor.cli import main


def test_cli_help() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Resume tailoring workflow commands" in result.output
    assert "tailor-job" in result.output


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
