"""Tests for cronwatch.healthcheck."""

from __future__ import annotations

import json
import urllib.request

import pytest

from cronwatch.healthcheck import HealthCheckServer
from cronwatch.metrics import MetricsRegistry


@pytest.fixture()
def registry() -> MetricsRegistry:
    reg = MetricsRegistry()
    reg.record_success("backup", duration=12.5)
    reg.record_failure("backup")
    return reg


@pytest.fixture()
def server(registry: MetricsRegistry):
    srv = HealthCheckServer(registry, host="127.0.0.1", port=19876)
    srv.start()
    yield srv
    srv.stop()


def _get(url: str) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, resp.read().decode()


def test_health_returns_200(server: HealthCheckServer) -> None:
    status, body = _get(f"{server.url}/health")
    assert status == 200
    data = json.loads(body)
    assert data["status"] == "ok"


def test_health_reports_job_count(server: HealthCheckServer) -> None:
    _, body = _get(f"{server.url}/health")
    data = json.loads(body)
    assert data["jobs"] == 1  # only "backup" registered


def test_metrics_prometheus_format(server: HealthCheckServer) -> None:
    status, body = _get(f"{server.url}/metrics")
    assert status == 200
    assert "cronwatch" in body
    assert "backup" in body


def test_metrics_text_format(server: HealthCheckServer) -> None:
    status, body = _get(f"{server.url}/metrics/text")
    assert status == 200
    assert "backup" in body


def test_unknown_path_returns_404(server: HealthCheckServer) -> None:
    import urllib.error
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _get(f"{server.url}/unknown")
    assert exc_info.value.code == 404


def test_stop_shuts_down_server(registry: MetricsRegistry) -> None:
    import socket
    srv = HealthCheckServer(registry, host="127.0.0.1", port=19877)
    srv.start()
    srv.stop()
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", 19877), timeout=1)
