from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

def system_prefers_dark() -> bool:
    app = QGuiApplication.instance()
    if app is None:
        return False
    try:
        scheme = app.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return True
        if scheme == Qt.ColorScheme.Light:
            return False
    except (AttributeError, TypeError):
        pass
    return False
