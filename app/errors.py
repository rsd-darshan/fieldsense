"""Central HTTP error handling — JSON on /api, plain text elsewhere."""

from __future__ import annotations

from flask import Flask, jsonify, request


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(500)
    def _server_error(_exc):
        app.logger.exception("unhandled server error path=%s", request.path)
        if request.path.startswith("/api"):
            return jsonify({"error": "internal_error"}), 500
        return "Internal Server Error", 500
