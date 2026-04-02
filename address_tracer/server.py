"""HTTP server exposing the address tracer service as REST API endpoints.

Uses only the standard library (http.server) so there are no extra dependencies.
For production use, wrap the service with Flask/FastAPI instead.

Endpoints:
    POST /correct          — correct a single address
    POST /correct/batch    — correct multiple addresses
    POST /evaluate         — run evaluation on posted golden records
    GET  /health           — health check
"""

from __future__ import annotations

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

from .service import AddressTracerService


class _Handler(BaseHTTPRequestHandler):
    service: AddressTracerService

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        return json.loads(raw) if raw else {}

    def do_GET(self):
        if self.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        try:
            body = self._read_body()

            if self.path == "/correct":
                address = body.get("address", "")
                result = self.service.correct(address)
                self._send_json(result)

            elif self.path == "/correct/batch":
                addresses = body.get("addresses", [])
                results = self.service.correct_batch(addresses)
                self._send_json({"results": results})

            elif self.path == "/evaluate":
                goldens = body.get("goldens", [])
                identifier = body.get("identifier", "")
                eval_result = self.service.evaluate_goldens(
                    goldens, identifier=identifier
                )
                self._send_json(eval_result.to_dict())

            else:
                self._send_json({"error": "not found"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def log_message(self, format, *args):
        print(f"[address-tracer] {args[0]}")


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Start the HTTP server."""
    handler = _Handler
    handler.service = AddressTracerService()
    server = HTTPServer((host, port), handler)
    print(f"Address Tracer service running on http://{host}:{port}")
    print("Endpoints:")
    print("  POST /correct        — correct a single address")
    print("  POST /correct/batch  — correct multiple addresses")
    print("  POST /evaluate       — evaluate against golden records")
    print("  GET  /health         — health check")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
