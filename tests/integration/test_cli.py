import pytest
from typer.testing import CliRunner
from talon.cli.main import app

runner = CliRunner()

def test_scan_no_scope():
    result = runner.invoke(app, ["scan", "example.com"])
    assert result.exit_code == 1
    assert "Error: You must pass --confirm-scope" in result.stdout

def test_collect_dns_no_scope():
    result = runner.invoke(app, ["collect", "dns", "example.com"])
    assert result.exit_code == 1
    assert "Error: You must pass --confirm-scope" in result.stdout

def test_export_no_scope_needed():
    # This should not fail with scope error
    result = runner.invoke(app, ["export", "example.com"])
    assert "Error: You must pass --confirm-scope" not in result.stdout
