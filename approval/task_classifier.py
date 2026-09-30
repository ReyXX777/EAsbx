from __future__ import annotations

from approval.models import (
    RiskLevel,
    TaskKind,
    TaskRequest,
)


def build_task_request(
    prompt: str,
) -> TaskRequest:
    """
    Convert the existing browser task prompt into the
    normalized representation consumed by the approval layer.

    This function is deterministic and contains no JEV calls.
    """

    normalized = prompt.strip().lower()

    kind = TaskKind.BROWSER

    requested_action = _infer_browser_action(
        normalized
    )

    risk_level = _infer_browser_risk(
        normalized,
        requested_action,
    )

    return TaskRequest(
        prompt=prompt.strip(),
        kind=kind,
        requested_action=requested_action,
        risk_level=risk_level,
    )


def _infer_browser_action(
    prompt: str,
) -> str:
    """
    Identify the broad browser operation.

    This intentionally does not attempt to understand the
    entire task semantically.
    """

    if any(
        phrase in prompt
        for phrase in (
            "download",
            "save file",
            "export",
        )
    ):
        return "download"

    if any(
        phrase in prompt
        for phrase in (
            "upload",
            "attach file",
        )
    ):
        return "upload"

    if any(
        phrase in prompt
        for phrase in (
            "submit",
            "purchase",
            "buy",
            "order",
            "send",
            "post",
            "publish",
        )
    ):
        return "external_side_effect"

    if any(
        phrase in prompt
        for phrase in (
            "delete",
            "remove",
            "cancel subscription",
        )
    ):
        return "destructive_action"

    if any(
        phrase in prompt
        for phrase in (
            "login",
            "log in",
            "sign in",
        )
    ):
        return "authentication"

    if any(
        phrase in prompt
        for phrase in (
            "extract",
            "scrape",
            "read",
            "find",
            "search",
            "navigate",
            "open",
        )
    ):
        return "read_navigation"

    return "browser_interaction"


def _infer_browser_risk(
    prompt: str,
    action: str,
) -> RiskLevel:

    if action == "destructive_action":
        return RiskLevel.CRITICAL

    if action in {
        "external_side_effect",
        "upload",
        "download",
    }:
        return RiskLevel.HIGH

    if action == "authentication":
        return RiskLevel.HIGH

    if action == "browser_interaction":
        return RiskLevel.MEDIUM

    return RiskLevel.LOW