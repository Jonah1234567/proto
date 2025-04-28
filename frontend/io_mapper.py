from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QComboBox, QWidget, QScrollArea, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt


class IOMapperDialog(QDialog):
    def __init__(self, block, parent=None):
        super().__init__(parent)
        self.block = block
        print(type(block.inputs))
        self.setWindowTitle(f"Map Inputs for: {self.block.name}")
        self.setMinimumSize(800, 647)

        self.input_mappings = {}

        main_layout = QVBoxLayout(self)

        title = QLabel("Select output values from other blocks to feed into this block’s inputs.")
        title.setStyleSheet("font-weight: bold; font-size: 16px; padding-bottom: 10px;")
        main_layout.addWidget(title)

        # === Scroll area setup ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # === Get upstream blocks
        upstream_blocks = []
        for conn in self.block.incoming_connections:
            if conn.end_block == self.block and conn.start_block not in upstream_blocks:
                upstream_blocks.append(conn.start_block)

        # === Inputs UI
        input_dict = self.block.inputs.to_dict()

        if not input_dict:
            scroll_layout.addWidget(QLabel("⚠️ This block has no defined inputs."))
        else:
            for input_name in input_dict.keys():
                row = QHBoxLayout()

                label = QLabel(f"{input_name}:")
                label.setFixedWidth(120)
                row.addWidget(label)

                dropdown = QComboBox()
                dropdown.addItem("— Not Connected —", userData=None)

                # Track current selection index
                selected_index = 0
                saved_link = getattr(self.block, "input_links", {}).get(input_name)

                for blk in upstream_blocks:
                    for out in blk.outputs.to_dict().keys():
                        label_str = f"{blk.name}.{out}"
                        user_data = (blk.id, out)
                        dropdown.addItem(label_str, userData=user_data)

                        if saved_link and saved_link["block_id"] == blk.id and saved_link["output"] == out:
                            selected_index = dropdown.count() - 1

                dropdown.setCurrentIndex(selected_index)
                self.input_mappings[input_name] = dropdown
                row.addWidget(dropdown)
                scroll_layout.addLayout(row)

        # === Save + Close buttons
        save_btn = QPushButton("Save Mappings")
        save_btn.setStyleSheet("color: black; border: 1px solid black;")
        save_btn.clicked.connect(self.save_mappings)
        main_layout.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel, QComboBox, QPushButton {
                color: black;
                background-color: white;
                font-size: 14px;
            }
            QComboBox {
                border: 1px solid gray;
                padding: 4px;
            }
            QPushButton {
                border: 1px solid black;
                padding: 6px;
                border-radius: 4px;
            }
            QScrollArea {
                background: white;
            }
        """)
        self.load_saved_mappings()


    def save_mappings(self):
        if not hasattr(self.block, "input_mappings"):
            self.block.input_mappings = {}  # Initialize if missing

        self.block.input_mappings.clear()  # Reset existing mappings

        for input_name, combo in self.input_mappings.items():
            index = combo.currentIndex()
            if index <= 0:
                continue  # Skip "Not Connected"

            data = combo.itemData(index)
            if isinstance(data, tuple) and len(data) == 2:
                self.block.input_mappings[input_name] = {
                    "block_id": data[0],
                    "output_name": data[1]
                }

        print("🔗 Saved input mappings:", self.block.input_mappings)

        # Optional: flash confirmation
        msg = QMessageBox(self)
        msg.setWindowTitle("Success")
        msg.setText("✅ Input mappings saved.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def load_saved_mappings(self):
        if not hasattr(self.block, "input_mappings"):
            return

        for input_name, dropdown in self.input_mappings.items():
            mapping = self.block.input_mappings.get(input_name)
            if not mapping:
                continue  # No saved mapping for this input

            target_block_id = mapping.get("block_id")
            target_output_name = mapping.get("output_name")

            # Try to find matching item in dropdown
            for idx in range(1, dropdown.count()):  # Start from 1 (skip "Not Connected")
                item_data = dropdown.itemData(idx)
                if item_data and isinstance(item_data, tuple):
                    block_id, output_name = item_data
                    if block_id == target_block_id and output_name == target_output_name:
                        dropdown.setCurrentIndex(idx)
                        break
