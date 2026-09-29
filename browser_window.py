# browser_window.py
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QWidget
)
from PySide6.QtCore import QUrl

# Fallback to standard webview if WebEngine is not bundled
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView as WebViewer
except ImportError:
    from PySide6.QtWidgets import QTextEdit as WebViewer

class BrowserWindowWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # Top Row: Mode Toggle Tabs (Browser / Files)
        top_tabs = QHBoxLayout()
        self.browser_tab_btn = QPushButton("Browser 🌐")
        self.files_tab_btn = QPushButton("Files 📁")
        
        tab_style = """
            QPushButton {
                border: 1px solid black;
                background-color: white;
                font-weight: bold;
                padding: 6px;
            }
        """
        self.browser_tab_btn.setStyleSheet(tab_style)
        self.files_tab_btn.setStyleSheet(tab_style)
        
        top_tabs.addWidget(self.browser_tab_btn)
        top_tabs.addWidget(self.files_tab_btn)
        main_layout.addLayout(top_tabs)
        
        # Sub Row: New Tab Button
        self.new_tab_btn = QPushButton("New Tab +")
        self.new_tab_btn.setFixedWidth(90)
        self.new_tab_btn.setStyleSheet("border: 1px solid black; background: white; font-size: 11px;")
        main_layout.addWidget(self.new_tab_btn)
        
        # Navigation Bar (Back/Forward/Refresh & URL bar)
        nav_bar = QHBoxLayout()
        self.nav_btn = QPushButton("⇆ 🔄")
        self.nav_btn.setStyleSheet("border: none; font-size: 14px;")
        
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or Enter Address")
        self.url_bar.setStyleSheet("border: 1px solid black; padding: 4px; font-size: 12px;")
        self.url_bar.returnPressed.connect(self.load_url)
        
        nav_bar.addWidget(self.nav_btn)
        nav_bar.addWidget(self.url_bar, stretch=1)
        main_layout.addLayout(nav_bar)
        
        # Browser View Context
        self.browser_view = WebViewer()
        if hasattr(self.browser_view, 'setUrl'):
            self.browser_view.setUrl(QUrl("https://www.google.com"))
        main_layout.addWidget(self.browser_view, stretch=1)

    def load_url(self):
        url_text = self.url_bar.text().strip()
        if not url_text.startswith("http://") and not url_text.startswith("https://"):
            url_text = "https://" + url_text
        if hasattr(self.browser_view, 'setUrl'):
            self.browser_view.setUrl(QUrl(url_text))