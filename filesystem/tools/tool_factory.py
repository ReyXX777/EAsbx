from __future__ import annotations

from ..compute.compute_service import ComputeService
from ..filesystem_service import SandboxFilesystemService
from .compute_tools import ComputeToolAdapter
from .filesystem_tools import FilesystemToolAdapter
from .tool_dispatcher import ToolDispatcher
from .tool_models import ToolSpec
from .tool_registry import ToolRegistry


def create_tool_registry(
    *,
    filesystem_service: SandboxFilesystemService,
    compute_service: ComputeService,
) -> ToolRegistry:
    """
    Create and populate the central tool registry.

    This function is the composition boundary for the tool layer.

    It knows which adapters belong to the application, but it does not
    contain any filesystem or compute implementation logic.
    """

    registry = ToolRegistry()

    filesystem_adapter = FilesystemToolAdapter(
        filesystem_service,
    )

    compute_adapter = ComputeToolAdapter(
        compute_service,
    )

    registry.register_many(
        _build_tool_specs(
            filesystem_adapter.build_tools(),
        )
    )

    registry.register_many(
        _build_tool_specs(
            compute_adapter.build_tools(),
        )
    )

    return registry


def create_tool_dispatcher(
    *,
    filesystem_service: SandboxFilesystemService,
    compute_service: ComputeService,
) -> ToolDispatcher:
    """
    Create the fully configured application tool dispatcher.

    This is the preferred entry point for callers that simply need
    a dispatcher capable of executing filesystem and compute tools.
    """

    registry = create_tool_registry(
        filesystem_service=filesystem_service,
        compute_service=compute_service,
    )

    return ToolDispatcher(
        registry,
    )


def _build_tool_specs(
    tools: list[tuple[str, str, dict, object]],
) -> list[ToolSpec]:
    """
    Convert adapter-provided tool definitions into ToolSpec objects.

    Adapter format:

        (
            name,
            description,
            declaration,
            handler,
        )
    """

    specs: list[ToolSpec] = []

    for (
        name,
        description,
        declaration,
        handler,
    ) in tools:
        specs.append(
            ToolSpec(
                name=name,
                description=description,
                declaration=declaration,
                handler=handler,
            )
        )

    return specs
