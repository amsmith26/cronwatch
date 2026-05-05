"""Tests for cronwatch.config module."""

import os
import textwrap
import pytest

from cronwatch.config import load_config, CronwatchConfig, JobConfig, AlertConfig


MINIMAL_YAML = textwrap.dedent("""\
    jobs:
      - name: test-job
        schedule: "* * * * *"
""")

FULL_YAML = textwrap.dedent("""\
    state_dir: /tmp/cronwatch_state
    log_file: /tmp/cronwatch.log
    check_interval: 30
    alerts:
      email: admin@example.com
      smtp_host: mail.example.com
      smtp_port: 465
      smtp_user: user
      smtp_password: pass
    jobs:
      - name: job-one
        schedule: "0 * * * *"
        timeout: 120
        alert_email: team@example.com
        max_retries: 2
      - name: job-two
        schedule: "0 0 * * *"
""")


@pytest.fixture
def tmp_yaml(tmp_path):
    def _write(content):
        p = tmp_path / "cronwatch.yaml"
        p.write_text(content)
        return str(p)
    return _write


def test_load_minimal_config(tmp_yaml):
    path = tmp_yaml(MINIMAL_YAML)
    cfg = load_config(path)
    assert isinstance(cfg, CronwatchConfig)
    assert len(cfg.jobs) == 1
    assert cfg.jobs[0].name == "test-job"
    assert cfg.jobs[0].schedule == "* * * * *"
    assert cfg.jobs[0].timeout == 3600
    assert cfg.check_interval == 60


def test_load_full_config(tmp_yaml):
    path = tmp_yaml(FULL_YAML)
    cfg = load_config(path)
    assert cfg.state_dir == "/tmp/cronwatch_state"
    assert cfg.log_file == "/tmp/cronwatch.log"
    assert cfg.check_interval == 30
    assert cfg.alerts.email == "admin@example.com"
    assert cfg.alerts.smtp_port == 465
    assert len(cfg.jobs) == 2
    job = cfg.jobs[0]
    assert job.name == "job-one"
    assert job.timeout == 120
    assert job.max_retries == 2
    assert job.alert_email == "team@example.com"


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/cronwatch.yaml")


def test_invalid_yaml_raises(tmp_yaml):
    path = tmp_yaml("- just\n- a\n- list")
    with pytest.raises(ValueError, match="YAML mapping"):
        load_config(path)


def test_default_alert_config(tmp_yaml):
    path = tmp_yaml(MINIMAL_YAML)
    cfg = load_config(path)
    assert cfg.alerts.smtp_host == "localhost"
    assert cfg.alerts.smtp_port == 25
    assert cfg.alerts.email is None
