"""Utility package.

Keep this module free of heavy imports and side effects.
"""

from app.utils.logging import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger"]
