from __future__ import annotations

from agent_result import AgentResult
from qt_theme import AgentResponseParser as ThemeAgentResponseParser
from qt_theme import ThemeManager


class AgentResponseParser:
    """
    Compatibility facade for agent-result presentation.

    The actual HTML structure is owned by qt_theme.AgentResponseParser.
    Theme state is supplied by the global ThemeManager.
    """

    @classmethod
    def parse_and_format(
        cls,
        result: AgentResult,
    ) -> str:
        """
        Render an AgentResult using the current global Qt theme.
        """
        theme = ThemeManager.instance()

        return ThemeAgentResponseParser.parse_and_format(
            result,
            theme.html,
        )
