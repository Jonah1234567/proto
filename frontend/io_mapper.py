from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class IOMapperDialog(QDialog):
    def __init__(self, block, tab_widget, parent=None):
        super().__init__(parent)
        self.block = block
        self.tab_widget = tab_widget

        self.setWindowTitle(f"Map Inputs for: {self.block.name}")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        
        title = QLabel("Select output values from other blocks to feed into this block’s inputs.")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)

        # TEMP: Show input names for now
        layout.addWidget(QLabel(f"Inputs: {self.block.inputs}"))

        # Add close/save buttons as needed
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
