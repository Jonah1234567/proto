from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPalette, QColor, QPainter, QBrush


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

        new_button = QPushButton("New Project")
        new_button.setIcon(QIcon("frontend/assets/new_project.png"))
        new_button.setIconSize(QSize(64, 64))
        new_button.setFixedSize(200, 300)
        new_button.setStyleSheet(self._button_stylesheet())
        new_button.clicked.connect(self.controller.switch_to_editor)

        load_button = QPushButton("Load Project")
        load_button.setIcon(QIcon("frontend/assets/load_project.png"))
        load_button.setIconSize(QSize(64, 64))
        load_button.setFixedSize(200, 300)
        load_button.setStyleSheet(self._button_stylesheet())
        load_button.clicked.connect(self.load_existing_project)

        tutorial_button = QPushButton("View Tutorial")
        tutorial_button.setIcon(QIcon("frontend/assets/tutorial.png"))
        tutorial_button.setIconSize(QSize(64, 64))
        tutorial_button.setFixedSize(200, 300)
        tutorial_button.setStyleSheet(self._button_stylesheet())
        ## This is not finished

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

    def load_existing_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Layout", "", "JSON Files (*.json)")
        if path:
            self.controller.editor_view.canvas.load_layout(path)
            self.controller.switch_to_editor()
