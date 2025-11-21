"""Compatibility wrapper exposing model helpers under src.backend.models.

Historically, model helpers for growth, energy, and traffic lived under
`src.backend.models`. They have since been moved to `src.models`, but this
module keeps the old import path working for tests and external callers.
"""

from src.models import *  # noqa: F401,F403
