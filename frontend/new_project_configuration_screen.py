from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFileDialog, QSpacerItem
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPalette, QColor, QPainter, QBrush

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QMouseEvent, QCursor
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QToolButton
from components.back_button import BackButton



class NewProjectConfigurationScreen(QWidget):
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

        title = QLabel("New Project Configuration")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold; padding: 20px;")

        blurb = QLabel("Please choose what type of project you would like create")
        blurb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blurb.setStyleSheet("font-size: 18px; padding-bottom: 40px;")

        # === Buttons ===
        button_row = QHBoxLayout()
        button_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_row.setSpacing(40)

        # NEW PROJECT button
        functional_project_button = QToolButton()
        functional_project_button.setText("Functional Project")
        functional_project_button.setIcon(QIcon("frontend/assets/functional_project.png"))
        functional_project_button.setIconSize(QSize(128, 128))
        functional_project_button.setFixedSize(200, 300)
        functional_project_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        functional_project_button.setStyleSheet("""
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
        functional_project_button.clicked.connect(self.controller.switch_to_editor)

        # LOAD PROJECT button
        infrastructure_project_button = QToolButton()
        infrastructure_project_button.setText("Infrastructure Project")
        infrastructure_project_button.setIcon(QIcon("frontend/assets/infrastructure_project.png"))
        infrastructure_project_button.setIconSize(QSize(128, 128))
        infrastructure_project_button.setFixedSize(200, 300)
        infrastructure_project_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        infrastructure_project_button.setStyleSheet("""
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
        infrastructure_project_button.clicked.connect(self.controller.switch_to_under_construction)


        button_row.addWidget(functional_project_button)
        button_row.addWidget(infrastructure_project_button)

        # Add widgets
        main_layout.addWidget(title)
        main_layout.addWidget(blurb)
        main_layout.addLayout(button_row)
        
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Bottom row for the button
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(BackButton(self.controller), alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_row.addStretch()  # pushes everything to the left

        main_layout.addLayout(bottom_row)
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
