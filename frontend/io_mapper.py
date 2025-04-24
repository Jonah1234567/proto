from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QComboBox, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt



class IOMapperDialog(QDialog):
    def __init__(self, block, tab_widget, canvas, parent=None):
        super().__init__(parent)
        self.block = block
        self.tab_widget = tab_widget
        self.canvas = canvas  # 👈 Pass in the canvas to get connections
        self.setWindowTitle(f"Map Inputs for: {self.block.name}")
        self.setMinimumSize(600, 500)

        self.input_mappings = {}  # {input_name: (block_id, output_name)}

        layout = QVBoxLayout(self)

        title = QLabel("Select output values from other blocks to feed into this block’s inputs.")
        title.setStyleSheet("font-weight: bold; font-size: 16px; padding-bottom: 10px;")
        layout.addWidget(title)

        # Scrollable area in case of many inputs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Step 1: Gather all blocks connected into this block
        upstream_blocks = []
        for conn in self.block.incoming_connections:
            if conn.end_block == self.block:
                upstream_blocks.append(conn.start_block)

        # Step 2: Build dropdowns per input
        for input_name in self.block.inputs:
            row = QHBoxLayout()

            label = QLabel(f"{input_name}:")
            label.setFixedWidth(100)
            row.addWidget(label)

            dropdown = QComboBox()
            dropdown.addItem("— Not Connected —", userData=None)

            for blk in upstream_blocks:
                for out in blk.outputs:
                    label_str = f"{blk.name}.{out}"
                    dropdown.addItem(label_str, userData=(blk.id, out))

            row.addWidget(dropdown)
            scroll_layout.addLayout(row)

            # Store reference to pull mapping on save
            self.input_mappings[input_name] = dropdown

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Save + Close
        save_btn = QPushButton("Save Mappings")
        save_btn.setStyleSheet("color: black; border: 1px solid black;")
        save_btn.clicked.connect(self.save_mappings)
        layout.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def save_mappings(self):
        self.block.input_links = {}  # Optional: where you store resolved links
        for input_name, combo in self.input_mappings.items():
            data = combo.currentData()
            if data:
                self.block.input_links[input_name] = {
                    "block_id": data[0],
                    "output": data[1]
                }

        print("🔗 Saved input mappings:", self.block.input_links)
        self.accept()
