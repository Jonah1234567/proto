from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QHBoxLayout, QMessageBox, QGroupBox,
    QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
import importlib.metadata
import sys
import subprocess
import threading
import requests
from PyQt6.QtWidgets import QLineEdit, QCompleter, QMessageBox
from PyQt6.QtCore import QTimer



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

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_directory)
        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(browse_button)
        env_layout.addRow("Save Directory:", dir_row)

        self.entry_input = QLineEdit()
        env_layout.addRow("Entry Block (optional):", self.entry_input)

        self.runtime_combo = QComboBox()
        self.runtime_combo.addItems(["Local CPU", "Local GPU", "Remote (Cloud)", "Edge Device"])
        env_layout.addRow("Runtime Target:", self.runtime_combo)

        env_box.setLayout(env_layout)
        main_layout.addWidget(env_box)

        # === Section 3: Installed Packages ===
        packages_box = QGroupBox("📦 Installed Packages")
        packages_layout = QVBoxLayout()

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search packages...")
        self.search_bar.textChanged.connect(self.filter_packages)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
        """)
        packages_layout.addWidget(self.search_bar)

        # Table
        self.package_table = QTableWidget(0, 2)
        self.package_table.setHorizontalHeaderLabels(["Package", "Version"])
        self.package_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.package_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: black;
                font-family: monospace;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                border: 1px solid #aaa;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #b0bec5;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        packages_layout.addWidget(self.package_table)

        # Refresh button
        refresh_button = QPushButton("🔄 Refresh Packages")
        refresh_button.setFixedWidth(200)
        refresh_button.clicked.connect(self.populate_installed_packages)
        packages_layout.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignRight)

        packages_box.setLayout(packages_layout)
        main_layout.addWidget(packages_box)

        self.populate_installed_packages()

        # === Section 4: Install New Package ===
        install_box = QGroupBox("📥 Install New Package")
        install_layout = QHBoxLayout()

        # Package search bar with auto-completion
        self.package_search = QLineEdit()
        self.package_search.setPlaceholderText("Search package name...")
        self.package_search.textChanged.connect(self.update_package_completions)

        # Version entry
        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("Version (optional)")

        # Install button
        install_button = QPushButton("📦 Install")
        install_button.clicked.connect(self.install_package)

        install_layout.addWidget(self.package_search)
        install_layout.addWidget(self.version_input)
        install_layout.addWidget(install_button)
        install_box.setLayout(install_layout)
        main_layout.addWidget(install_box)

        # Set up completer
        self.package_completer = QCompleter()
        self.package_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.package_search.setCompleter(self.package_completer)



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

    def populate_installed_packages(self):
        self.package_table.setRowCount(0)
        try:
            packages = sorted(importlib.metadata.distributions(), key=lambda d: d.metadata['Name'].lower())
            for dist in packages:
                name = dist.metadata['Name']
                version = dist.version
                row = self.package_table.rowCount()
                self.package_table.insertRow(row)
                self.package_table.setItem(row, 0, QTableWidgetItem(name))
                self.package_table.setItem(row, 1, QTableWidgetItem(version))
        except Exception as e:
            self.package_table.setRowCount(1)
            self.package_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.package_table.setItem(0, 1, QTableWidgetItem(str(e)))

    def filter_packages(self, text):
        text = text.lower()
        for row in range(self.package_table.rowCount()):
            name_item = self.package_table.item(row, 0)
            version_item = self.package_table.item(row, 1)
            row_text = (name_item.text() + version_item.text()).lower()
            self.package_table.setRowHidden(row, text not in row_text)

    def install_package(self):
        name = self.package_search.text().strip()
        version = self.version_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Missing Package", "Please enter a package name.")
            return

        package = f"{name}=={version}" if version else name

        def run_install():
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True, text=True
            )

            def handle_result():
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", f"Installed: {package}")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to install:\n{result.stderr}")
                self.populate_installed_packages()

            QTimer.singleShot(0, handle_result)

        threading.Thread(target=run_install).start()


    def update_package_completions(self):
        query = self.package_search.text().strip()
        if not query:
            return

        def fetch():
            try:
                resp = requests.get(f"https://pypi.org/search/?q={query}", headers={"Accept": "application/vnd.pypi.simple.v1+json"})
                if resp.status_code == 200:
                    data = resp.json()
                    names = [pkg["name"] for pkg in data.get("projects", [])]
                    self.package_completer.model().setStringList(names)
            except Exception:
                pass

        threading.Thread(target=fetch).start()




