from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QHBoxLayout, QMessageBox, QFrame
)


class HadronProjectConfiguration(QWidget):
    def __init__(self, controller, tab_widget):
        super().__init__()
        self.controller = controller
        self.tab_widget = tab_widget
        self.setStyleSheet("color: black;")

        # === Outer layout for this tab ===
        outer_layout = QVBoxLayout(self)

        # === Bordered Frame (like canvas border) ===
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Shape.Box)
        self.frame.setLineWidth(2)
        self.frame.setStyleSheet("""
            QFrame {
                border: 2px solid #dcdde1;
                border-radius: 10px;
                background-color: white;
            }
        """)

        inner_layout = QVBoxLayout(self.frame)

        # === Project Name ===
        inner_layout.addWidget(QLabel("Project Name:"))
        self.name_input = QLineEdit()
        inner_layout.addWidget(self.name_input)

        # === Save Directory ===
        inner_layout.addWidget(QLabel("Save Directory:"))
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_button)
        inner_layout.addLayout(dir_layout)

        # === Entry Block ===
        inner_layout.addWidget(QLabel("Entry Block (optional):"))
        self.entry_input = QLineEdit()
        inner_layout.addWidget(self.entry_input)

        # === Runtime Target ===
        inner_layout.addWidget(QLabel("Runtime Target:"))
        self.runtime_combo = QComboBox()
        self.runtime_combo.addItems(["Local CPU", "Local GPU", "Remote (Cloud)", "Edge Device"])
        inner_layout.addWidget(self.runtime_combo)

        # === Create Project Button ===
        self.create_button = QPushButton("🚀 Create Project")
        self.create_button.setStyleSheet("""
            font-size: 14px;
            color: black;
            border: 2px solid black;
            border-radius: 6px;
            padding: 6px 12px;
        """)
        self.create_button.clicked.connect(self.create_project)
        inner_layout.addWidget(self.create_button)

        # Add frame to the main layout
        outer_layout.addWidget(self.frame)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.dir_input.setText(directory)

    def create_project(self):
        name = self.name_input.text().strip()
        path = self.dir_input.text().strip()
        entry = self.entry_input.text().strip()
        runtime = self.runtime_combo.currentText()

        if not name or not path:
            QMessageBox.warning(self, "Missing Info", "Please enter both project name and save directory.")
            return

        self.controller.start_project(
            name=name,
            path=path,
            entry_block=entry,
            runtime_target=runtime
        )