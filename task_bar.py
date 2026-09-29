# task_bar.py
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QListWidget, QStyle
from PySide6.QtCore import Qt

class TaskBarWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # New Task Button
        self.new_task_btn = QPushButton("New Task +")
        self.new_task_btn.setFixedHeight(45)
        self.new_task_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid black;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        
        # List to hold historical/active tasks
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("border: none; background: transparent;")
        
        layout.addWidget(self.new_task_btn)
        layout.addWidget(self.task_list)