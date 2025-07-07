from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QSize

class BackButton(QPushButton):
    def __init__(self, controller):
        super().__init__("← Back")
        self.setFixedSize(QSize(100, 40))
        self.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                background-color: #dddddd;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #cccccc;
            }
        """)
        self.clicked.connect(controller.switch_back)
