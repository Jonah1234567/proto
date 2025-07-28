from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPalette, QColor, QPainter, QBrush

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QMouseEvent, QCursor
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QToolButton
from components.file_dialogue import prompt_load_project_folder


import sys
from pathlib import Path

class WelcomeScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.setWindowTitle("Proto")
        self.setGeometry(100, 100, 1200, 800)

        # === Force white background with stylesheet AND fallback paint event ===
        self.setStyleSheet("background-color: white; color: black;")

        # === Main layout ===
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Welcome to Proto")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold; padding: 20px;")

        blurb = QLabel("Start a new project or load an existing one to begin creating.")
        blurb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blurb.setStyleSheet("font-size: 18px; padding-bottom: 40px;")

        # === Buttons ===
        button_row = QHBoxLayout()
        button_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_row.setSpacing(40)

        # NEW PROJECT button
        new_button = QToolButton()
        new_button.setText("New Project")
        new_button.setIcon(QIcon("frontend/assets/new_project.png"))
        new_button.setIconSize(QSize(64, 64))
        new_button.setFixedSize(200, 300)
        new_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        new_button.setStyleSheet("""
            QToolButton {
                background-color: white;
                border: 2px solid black;
                border-radius: 20px;
                font-size: 16px;
                padding-top: 100px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        new_button.clicked.connect(self.controller.switch_to_new_project_configuration)

        # LOAD PROJECT button
        load_button = QToolButton()
        load_button.setText("Load Project")
        load_button.setIcon(QIcon("frontend/assets/load_project.png"))
        load_button.setIconSize(QSize(64, 64))
        load_button.setFixedSize(200, 300)
        load_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        load_button.setStyleSheet("""
            QToolButton {
                background-color: white;
                border: 2px solid black;
                border-radius: 20px;
                font-size: 16px;
                padding-top: 100px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        load_button.clicked.connect(self.controller.switch_to_existing_project)

        # VIEW TUTORIAL button
        tutorial_button = QToolButton()
        tutorial_button.setText("View Tutorial")
        tutorial_button.setIcon(QIcon("frontend/assets/tutorial.png"))
        tutorial_button.setIconSize(QSize(64, 64))
        tutorial_button.setFixedSize(200, 300)
        tutorial_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        tutorial_button.setStyleSheet("""
            QToolButton {
                background-color: white;
                border: 2px solid black;
                border-radius: 20px;
                font-size: 16px;
                padding-top: 100px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)
        tutorial_button.clicked.connect(self.controller.switch_to_under_construction)

        button_row.addWidget(new_button)
        button_row.addWidget(load_button)
        button_row.addWidget(tutorial_button)

        # Add widgets
        main_layout.addWidget(title)
        main_layout.addWidget(blurb)
        main_layout.addLayout(button_row)
        self.setLayout(main_layout)

    def _button_stylesheet(self):
        return """
            QPushButton {
                font-size: 16px;
                text-align: bottom;
                padding: 10px;
                border: 2px solid black;
                border-radius: 12px;
                background-color: white;
                color: black;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """

    def paintEvent(self, event):
        # Fallback guarantee: manually paint white background
        painter = QPainter(self)
        painter.setBrush(QBrush(QColor("white")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())


