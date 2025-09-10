from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QInputDialog, QMessageBox, QGroupBox, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal
import re
from io_mapper import IOMapperDialog 

import sys
from pathlib import Path
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

sys.path.append(str(Path(__file__).resolve().parents[2]))


from backend.inputs_proxy import InputsProxy
from backend.outputs_proxy import OutputsProxy
from backend.saving import save_to_template

from frontend.block_editors.requirements_editor import RequirementsEditor

class BlockEditor(QWidget):
    modified = pyqtSignal()
    saved = pyqtSignal()
    def __init__(self, block, tab_widget, canvas):
        super().__init__()
        self.block = block
        self.canvas = canvas
        self.tab_widget = tab_widget
        self.setStyleSheet("color: black;")

        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Block Name:"))
        self.name_input = QLineEdit(block.name)
        self.name_input.textChanged.connect(self.modified.emit)
        self.layout.addWidget(self.name_input)

        self.layout.addWidget(QLabel("Code:"))
        self.code_input = QTextEdit()
        self.code_input.setPlainText(block.code)  # preserves newlines and tabs
        self.code_input.textChanged.connect(self.modified.emit)
        self.layout.addWidget(self.code_input)

        self.code_input.setStyleSheet("""
        QTextEdit {
            background: white;
            color: black;
            font-family: Consolas, monospace;
            font-size: 13px;
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 4px;
        }

        QScrollBar:vertical {
            border: none;
            background: #f0f0f0;
            width: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical {
            background: #b0bec5;
            min-height: 20px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical:hover {
            background: #90a4ae;
        }

        QScrollBar::handle:vertical:pressed {
            background: #78909c;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        """)


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

        auto_btn = QPushButton("🔁 Auto-Connect Matching I/O")
        auto_btn.setStyleSheet("""
            font-size: 14px;
            color: black;
            border: 2px solid black;
            border-radius: 6px;
            padding: 6px 12px;
        """)
        auto_btn.clicked.connect(self.auto_connect_matching_io)
        self.layout.addWidget(auto_btn)


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

        save_block_button = QPushButton("💾 Save Block to File")
        save_block_button.setStyleSheet("""
            font-size: 14px;
            color: black;
            border: 2px solid black;
            border-radius: 6px;
            padding: 6px 12px;
        """)
        save_block_button.clicked.connect(lambda: save_to_template(block))
        self.layout.addWidget(save_block_button)


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

        self.req_editor = RequirementsEditor(
            self,
            block=self.block,           # loads from block.requirements by default
            attr_name="requirements",   # or "dependencies" if you prefer that name
            title="Requirements (pip packages)",
        )
        self.req_editor.modified.connect(self.modified.emit)  # bubble up edits
        self.layout.addWidget(self.req_editor)

        self.block.requirements = self.req_editor.get_requirements()
        self.block.update()






    def add_input(self):
        self.modified.emit()
        text, ok = QInputDialog.getText(self, "New Input", "Input name:")
        if ok and text:
            self.input_list.addItem(QListWidgetItem(text))

    def add_output(self):
        self.modified.emit()
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
        # === Save requirements
        self.block.requirements = self.req_editor.get_requirements()

        self.block.update()
        print(f"💾 Saved block '{self.block.name}'")
        self.saved.emit()


    def open_io_mapper(self):
        
        print(type(self.block.inputs), "inputs")
        dialog = IOMapperDialog(self.block, self.tab_widget)
        dialog.exec()  # ✅ Modal dialog that blocks correctly until closed
        print(self.block.input_mappings)
        print("✅ IOMapperDialog closed successfully.")

    def auto_connect_matching_io(self):
        self.modified.emit()
        if not hasattr(self.block, "input_mappings"):
            self.block.input_mappings = {}

        self.block.input_mappings.clear()

        output_var_map = {}
        for conn in self.block.incoming_connections:
            blk = conn.start_block
            for out_name in blk.outputs.to_dict().keys():
                output_var_map.setdefault(out_name, []).append((blk.id, out_name, blk.name))

        collisions = []

        for input_name in self.block.inputs.to_dict().keys():
            var_name = input_name.split('.')[-1]

            matches = output_var_map.get(var_name, [])
            if len(matches) == 1:
                block_id, output_name, _ = matches[0]
                self.block.input_mappings[input_name] = {
                    "block_id": block_id,
                    "output_name": output_name
                }
            elif len(matches) > 1:
                collisions.append(var_name)

        # Show a popup or log result
        if collisions:
            QMessageBox.warning(
                self,
                "Namespace Collision",
                f"The following variable names appear in multiple upstream blocks:\n\n" +
                "\n".join(f"• {name}" for name in collisions)
            )
        else:
            QMessageBox.information(self, "Auto-Connect", "Auto-connection completed successfully.")

    def _maybe_save_changes(self):
        if self.tab_widget.currentWidget() is self:
            self.save_changes()
