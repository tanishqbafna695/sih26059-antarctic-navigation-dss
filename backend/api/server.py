"""Module-level app for `uvicorn backend.api.server:app`.

This allows: uvicorn backend.api.server:app --host 127.0.0.1 --port 8000
"""
from backend.api.app import create_app

app = create_app()
