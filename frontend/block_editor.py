from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QInputDialog
)
import re
from io_mapper import IOMapperDialog 

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.inputs_proxy import InputsProxy
from backend.outputs_proxy import OutputsProxy

class BlockEditor(QWidget):
    def __init__(self, block, tab_widget):
        super().__init__()
        self.block = block
        self.tab_widget = tab_widget
        self.setStyleSheet("color: black;")

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Block Name:"))
        self.name_input = QLineEdit(block.name)
        self.layout.addWidget(self.name_input)

        self.layout.addWidget(QLabel("Code:"))
        self.code_input = QTextEdit()
        self.code_input.setPlainText(block.code)  # preserves newlines and tabs
        self.layout.addWidget(self.code_input)

        self.layout.addWidget(QLabel("Inputs:"))
        self.input_list = QListWidget()
        inputs = block.inputs.to_list()
        self.input_list.addItems(inputs)
        self.layout.addWidget(self.input_list)


        self.layout.addWidget(QLabel("Outputs:"))
        self.output_list = QListWidget()
        outputs = block.outputs.to_list()
        self.output_list.addItems(outputs)
        self.layout.addWidget(self.output_list)

        # Mapping Button
        map_inputs_button = QPushButton("🔗 Open I/O Mapper")
        map_inputs_button.setStyleSheet("""
            font-size: 14px;
            color: black;
            border: 2px solid black;
            border-radius: 6px;
            padding: 6px 12px;
        """)
        map_inputs_button.clicked.connect(self.open_io_mapper)
        self.layout.addWidget(map_inputs_button)


        # === Connected Blocks: BEFORE ===
        self.layout.addWidget(QLabel("Blocks Before (inputs):"))
        before_list = QListWidget()
        for conn in self.block.incoming_connections:
            source = conn.start_block
            before_list.addItem(source.name)
        before_list.setDisabled(True)
        self.layout.addWidget(before_list)

        # === Connected Blocks: AFTER ===
        self.layout.addWidget(QLabel("Blocks After (outputs):"))
        after_list = QListWidget()
        for conn in self.block.outgoing_connections:
            dest = conn.end_block
            after_list.addItem(dest.name)
        after_list.setDisabled(True)
        self.layout.addWidget(after_list)


    def add_input(self):
        text, ok = QInputDialog.getText(self, "New Input", "Input name:")
        if ok and text:
            self.input_list.addItem(QListWidgetItem(text))

    def add_output(self):
        text, ok = QInputDialog.getText(self, "New Output", "Output name:")
        if ok and text:
            self.output_list.addItem(QListWidgetItem(text))

    def save_changes(self):
        self.block.name = self.name_input.text()
        self.tab_widget.setTabText(self.tab_widget.indexOf(self), self.block.name)
        self.block.update()

        self.block.code = self.code_input.toPlainText()

        # === Extract inputs and outputs from code
        code = self.block.code

        input_matches = re.findall(r"\binputs\.([a-zA-Z_][a-zA-Z0-9_]*)", code)
        output_matches = re.findall(r"\boutputs\.([a-zA-Z_][a-zA-Z0-9_]*)", code)

        # Deduplicate and preserve order
        inputs = list(dict.fromkeys(input_matches))
        outputs = list(dict.fromkeys(output_matches))

        # === Update UI lists
        self.input_list.clear()
        self.block.inputs = InputsProxy()
        for inp in inputs:
            self.input_list.addItem(inp)

        self.output_list.clear()
        self.block.outputs = OutputsProxy()
        for out in outputs:
            self.output_list.addItem(out)

        # === Update block data
        self.block.inputs.set_names(inputs)
        self.block.outputs.set_names(outputs)
        self.block.update()


    def open_io_mapper(self):
        
        print(type(self.block.inputs), "inputs")
        dialog = IOMapperDialog(self.block, self.tab_widget)
        dialog.exec()  # ✅ Modal dialog that blocks correctly until closed
        print(self.block.input_mappings)
        print("✅ IOMapperDialog closed successfully.")

        

