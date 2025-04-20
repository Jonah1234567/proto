from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMainWindow
)
from PyQt6.QtCore import Qt
from canvas import Canvas
from block import Block
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proto")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        title = QLabel("Proto")
        title.setStyleSheet("font-size: 36px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()  # push right

        self.add_block_button = QPushButton("➕ Add Block")
        self.add_block_button.setFixedWidth(200)
        self.add_block_button.setStyleSheet("""
            font-size: 16px;
            padding: 10px;
            color: black;
            border: 2px solid black;
            border-radius: 8px;
        """)
        self.add_block_button.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom_row.addWidget(self.add_block_button)
        bottom_row.setContentsMargins(0, 10, 10, 10)  # padding from edges

        self.canvas = Canvas()
        # Assemble layout
        layout.addWidget(title)
        layout.addWidget(self.canvas)
        layout.addLayout(bottom_row)

        self.setCentralWidget(central_widget)
        self.add_block_button.clicked.connect(self.canvas.add_block)

        with open("./frontend/styles.qss", "r") as f:
            self.setStyleSheet(f.read())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
