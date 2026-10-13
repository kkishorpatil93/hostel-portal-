"""Tests for application configuration environments."""

import pytest

from config import DevelopmentConfig, ProductionConfig, TestingConfig


def test_development_config():
    assert DevelopmentConfig.DEBUG is True
    assert DevelopmentConfig.TESTING is False
    assert DevelopmentConfig.SESSION_COOKIE_SECURE is False


def test_testing_config():
    assert TestingConfig.TESTING is True
    assert TestingConfig.DEBUG is False
    assert TestingConfig.WTF_CSRF_ENABLED is False
    assert TestingConfig.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"


def test_production_config_rejects_weak_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "short-secret")
    with pytest.raises(ValueError, match="CRITICAL SECURITY ERROR"):
        ProductionConfig.init_app(None)


def test_production_config_accepts_strong_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "a" * 32)
    # Should not raise
    ProductionConfig.init_app(None)
