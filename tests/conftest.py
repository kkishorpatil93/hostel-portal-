"""Pytest fixtures for StayNest PG platform."""

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture(autouse=True)
def app():
    """Create application configured for testing with an in-memory SQLite database and pushed app context."""
    app_instance = create_app("testing")
    ctx = app_instance.app_context()
    ctx.push()
    db.create_all()

    yield app_instance

    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
