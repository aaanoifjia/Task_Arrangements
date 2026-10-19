"""Explicit FastAPI application construction."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Construct the local API without opening resources or starting a server."""
    return FastAPI(title="Codex Flow Local API", version="0.1.0")
