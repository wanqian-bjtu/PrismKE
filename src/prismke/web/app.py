"""Compatibility import; the Gradio implementation lives in frontend.app."""

from frontend.app import mount_gradio

__all__ = ["mount_gradio"]
