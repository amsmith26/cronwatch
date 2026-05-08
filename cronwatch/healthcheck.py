"""Simple HTTP health-check endpoint that exposes live metrics."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from cronwatch.metrics import MetricsRegistry
from cronwatch.metrics_export import render_prometheus, render_text


class _Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler serving /health, /metrics, and /metrics/text."""

    registry: MetricsRegistry  # injected by HealthCheckServer

    def log_message(self, fmt: str, *args: object) -> None:  # silence default logging
        pass

    def _send(self, status: int, content_type: str, body: str) -> None:
        encoded = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            payload = {"status": "ok", "jobs": len(self.registry.all())}
            self._send(200, "application/json", json.dumps(payload))
        elif self.path == "/metrics":
            self._send(200, "text/plain; version=0.0.4", render_prometheus(self.registry))
        elif self.path == "/metrics/text":
            self._send(200, "text/plain", render_text(self.registry))
        else:
            self._send(404, "text/plain", "not found")


class HealthCheckServer:
    """Threaded HTTP server exposing health and metrics endpoints."""

    def __init__(self, registry: MetricsRegistry, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.registry = registry
        self.host = host
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the HTTP server in a background daemon thread."""
        handler = type("_BoundHandler", (_Handler,), {"registry": self.registry})
        self._server = HTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Shutdown the HTTP server gracefully."""
        if self._server:
            self._server.shutdown()
            self._server = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"
