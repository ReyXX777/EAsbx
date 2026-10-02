"""
Generic tool infrastructure for the filesystem agent.

This package provides:

    tool_models.py
        Generic tool-call and tool-result models.

    tool_registry.py
        Registration and discovery of available tools.

    tool_dispatcher.py
        Central routing of tool calls.

    filesystem_tools.py
        Adapters between generic tools and SandboxFilesystemService.

    compute_tools.py
        Adapters between generic tools and ComputeService.

The tools package intentionally contains no Gemini API logic.
"""

from .compute_tools import ComputeToolAdapter
from .filesystem_tools import FilesystemToolAdapter
from .tool_dispatcher import ToolDispatcher
from .tool_models import ToolCall, ToolResult, ToolSpec
from .tool_registry import ToolRegistry

__all__ = [
    "ComputeToolAdapter",
    "FilesystemToolAdapter",
    "ToolCall",
    "ToolDispatcher",
    "ToolRegistry",
    "ToolResult",
    "ToolSpec",
]
