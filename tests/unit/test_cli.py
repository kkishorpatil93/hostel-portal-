"""Tests for CLI commands: create-owner, seed-demo, generate-rent."""

from app.models.property import Room
from app.models.user import User, UserRole


def test_cli_create_owner(runner):
    result = runner.invoke(
        args=["create-owner"],
        input="CLI Owner\ncli.owner@example.com\n9876500000\nCliPass#2026\nCliPass#2026\n",
    )
    assert result.exit_code == 0
    assert "Success: Owner account 'cli.owner@example.com' created successfully!" in result.output

    owner = User.query.filter_by(email="cli.owner@example.com").first()
    assert owner is not None
    assert owner.role == UserRole.OWNER
    assert owner.check_password("CliPass#2026") is True


def test_cli_seed_demo_in_development(runner):
    result = runner.invoke(args=["seed-demo"])
    assert result.exit_code == 0
    assert "Demo seed completed successfully!" in result.output

    assert Room.query.count() >= 4
    owner = User.query.filter_by(email="owner@staynest.local").first()
    assert owner is not None
    assert owner.role == UserRole.OWNER


def test_cli_generate_rent(runner):
    # First seed demo to have an active allocation
    runner.invoke(args=["seed-demo"])

    # Run generate-rent for November 2026
    result = runner.invoke(args=["generate-rent", "--month", "2026-11"])
    assert result.exit_code == 0
    assert "Rent generation complete" in result.output

    # Running second time should skip existing charges (idempotent)
    result_second = runner.invoke(args=["generate-rent", "--month", "2026-11"])
    assert result_second.exit_code == 0
    assert "0 charges created" in result_second.output
    assert "skipped" in result_second.output
