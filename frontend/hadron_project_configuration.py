from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QHBoxLayout, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt

class HadronProjectConfiguration(QWidget):
    def __init__(self, controller, tab_widget):
        super().__init__()
        self.controller = controller
        self.tab_widget = tab_widget
        self.setStyleSheet("color: black;")

        # === Main Layout ===
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Section 1: Project Overview ===
        overview_box = QGroupBox("📁 Project Overview")
        overview_layout = QFormLayout()

        self.name_input = QLineEdit()
        overview_layout.addRow("Project Name:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Hadron", "Quantum", "Neural", "Classic"])
        overview_layout.addRow("Project Type:", self.type_combo)

        overview_box.setLayout(overview_layout)
        main_layout.addWidget(overview_box)

        # === Section 2: Environment Setup ===
        env_box = QGroupBox("⚙️ Environment Setup")
        env_layout = QFormLayout()

        # Save Directory
        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_directory)
        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(browse_button)
        env_layout.addRow("Save Directory:", dir_row)

        # Entry block
        self.entry_input = QLineEdit()
        env_layout.addRow("Entry Block (optional):", self.entry_input)

        # Runtime target
        self.runtime_combo = QComboBox()
        self.runtime_combo.addItems(["Local CPU", "Local GPU", "Remote (Cloud)", "Edge Device"])
        env_layout.addRow("Runtime Target:", self.runtime_combo)

        env_box.setLayout(env_layout)
        main_layout.addWidget(env_box)


    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.dir_input.setText(directory)

    def create_project(self):
        name = self.name_input.text().strip()
        path = self.dir_input.text().strip()
        entry = self.entry_input.text().strip()
        runtime = self.runtime_combo.currentText()
        project_type = self.type_combo.currentText()

        if not name or not path:
            QMessageBox.warning(self, "Missing Info", "Please enter both project name and save directory.")
            return

        self.controller.start_project(
            name=name,
            path=path,
            entry_block=entry,
            runtime_target=runtime,
            project_type=project_type
        )
