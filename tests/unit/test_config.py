import os
import yaml
import pytest
from talon.config import TalonConfig

def test_default_config(monkeypatch):
    monkeypatch.delenv("TALON_TRANSPORT__TIMEOUT", raising=False)
    config = TalonConfig.load_config()
    assert config.transport.timeout == 30
    assert config.rate_limiting.base_delay == 1.5

def test_yaml_load(tmp_path, monkeypatch):
    monkeypatch.delenv("TALON_TRANSPORT__TIMEOUT", raising=False)
    d = tmp_path / "config"
    d.mkdir()
    config_file = d / "test.yaml"
    config_file.write_text("transport:\n  timeout: 45\nrate_limiting:\n  base_delay: 2.0")

    config = TalonConfig.load_config(str(config_file))
    assert config.transport.timeout == 45
    assert config.rate_limiting.base_delay == 2.0
    # Check that defaults are preserved for missing keys
    assert config.transport.max_retries == 3

def test_env_var_override(monkeypatch):
    monkeypatch.setenv("TALON_TRANSPORT__TIMEOUT", "60")
    config = TalonConfig.load_config()
    assert config.transport.timeout == 60
