from dataclasses import dataclass
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget

@dataclass(frozen=True)
class ResponsiveMetrics:
    scale: float = 1.0

    @staticmethod
    def for_widget(widget: QWidget | None) -> "ResponsiveMetrics":
        if widget is None:
            return ResponsiveMetrics()
        dpi = widget.logicalDpiX() or 96.0
        dpi_scale = max(0.85, min(1.35, dpi / 96.0))
        width = max(320, widget.width())
        width_scale = 0.92 if width < 700 else 1.0 if width < 1500 else 1.06
        return ResponsiveMetrics(dpi_scale * width_scale)

    def px(self, value: int, minimum: int = 0) -> int:
        return max(minimum, round(value * self.scale))

    def margin(self) -> int: return self.px(10, 6)
    def spacing(self) -> int: return self.px(8, 4)
    def control_height(self) -> int: return self.px(32, 28)
    def compact_control_height(self) -> int: return self.px(28, 24)
    def radius(self) -> int: return self.px(6, 4)
    def sidebar_width(self) -> int: return self.px(240, 190)
    def panel_min_width(self) -> int: return self.px(280, 220)
    def splitter_handle(self) -> int: return self.px(5, 3)

    def icon_size(self) -> QSize:
        n = self.px(18, 14)
        return QSize(n, n)
