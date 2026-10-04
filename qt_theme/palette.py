from dataclasses import dataclass

@dataclass(frozen=True)
class ThemePalette:
    window: str
    surface: str
    surface_alt: str
    surface_elevated: str
    input: str
    border: str
    border_strong: str
    text: str
    text_muted: str
    text_disabled: str
    text_inverse: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_soft: str
    success: str
    success_soft: str
    warning: str
    warning_soft: str
    danger: str
    danger_soft: str
    info: str
    info_soft: str
    selection: str
    selection_text: str
    focus: str
    scrollbar: str
    scrollbar_hover: str
    live: str
    running: str
    completed: str
    failed: str
    cancelled: str

LIGHT = ThemePalette(
    "#F5F7FA","#FFFFFF","#F1F4F8","#FFFFFF","#FFFFFF","#D8DEE8","#B8C2D1",
    "#172033","#5E6878","#9AA3B2","#FFFFFF","#2563EB","#1D4ED8","#1E40AF",
    "#DBEAFE","#15803D","#DCFCE7","#B45309","#FEF3C7","#DC2626","#FEE2E2",
    "#0369A1","#E0F2FE","#DBEAFE","#172033","#2563EB","#C4CBD6","#9CA6B5",
    "#16A34A","#2563EB","#16A34A","#DC2626","#B45309"
)

DARK = ThemePalette(
    "#0F1117","#171A21","#1D222B","#202630","#141820","#303744","#46505F",
    "#F1F5F9","#A8B1BF","#687281","#0F1117","#60A5FA","#93C5FD","#BFDBFE",
    "#172B46","#4ADE80","#123522","#FBBF24","#3A2D0C","#F87171","#421A1A",
    "#38BDF8","#0B3040","#23456F","#F8FAFC","#60A5FA","#4B5563","#687386",
    "#4ADE80","#60A5FA","#4ADE80","#F87171","#FBBF24"
)

def palette_for_dark(dark: bool) -> ThemePalette:
    return DARK if dark else LIGHT
