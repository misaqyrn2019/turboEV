"""Vercel ASGI entrypoint. All /api requests are routed here by vercel.json."""
from backend.app import app

__all__ = ['app']
