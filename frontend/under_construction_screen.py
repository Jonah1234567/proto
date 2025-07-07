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



class UnderConstructionScreen(QWidget):
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

        title = QLabel("Under Construction")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 48px; font-weight: bold; padding: 20px;")
        
       
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Bottom row for the button
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(BackButton(self.controller), alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_row.addStretch()  # pushes everything to the left


        

        # Add widgets
        main_layout.addWidget(title)
        main_layout.addLayout(bottom_row)
        self.setLayout(main_layout)