"""piiscan — part of the Cognis Neural Suite."""

# Public constants — defined here so every import path finds them.
TOOL_NAME: str = "piiscan"
TOOL_VERSION: str = "0.1.0"

try:  # re-export the tool's public API from core
    from piiscan.core import *  # noqa: F401,F403
except Exception:  # pragma: no cover
    pass

__version__ = TOOL_VERSION
