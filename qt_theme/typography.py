from dataclasses import dataclass
from PySide6.QtGui import QFont, QFontDatabase

@dataclass(frozen=True)
class ThemeTypography:
    families: tuple[str, ...] = (
        "Noto Sans", "Noto Sans CJK SC", "Noto Sans CJK TC",
        "Noto Sans CJK JP", "Noto Sans Devanagari", "Segoe UI",
        "Arial", "Sans Serif",
    )
    monospace_families: tuple[str, ...] = (
        "JetBrains Mono", "Cascadia Code", "Cascadia Mono",
        "Noto Sans Mono", "Consolas", "Monospace",
    )
    base_size: int = 10
    small_size: int = 9
    title_size: int = 14
    metric_size: int = 18

    def family(self) -> str:
        available = set(QFontDatabase.families())
        return next((x for x in self.families if x in available), "Sans Serif")

    def monospace(self) -> str:
        available = set(QFontDatabase.families())
        return next((x for x in self.monospace_families if x in available), "Monospace")

    def base_font(self) -> QFont:
        font = QFont(self.family())
        font.setPointSize(self.base_size)
        return font

    def mono_font(self) -> QFont:
        font = QFont(self.monospace())
        font.setPointSize(self.base_size)
        return font
