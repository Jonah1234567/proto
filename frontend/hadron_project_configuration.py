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
import json
from PyQt6.QtWidgets import QMenu


from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt
from pathlib import Path
from PyQt6.QtCore import Qt, QStringListModel, QTimer
import threading, requests
import re, threading, requests
from PyQt6.QtCore import QTimer, QStringListModel, Qt
try:
    from packaging.version import Version as _SemVer
    from packaging.utils import canonicalize_name as _canon
except Exception:
    _SemVer = None
    def _canon(s):  # minimal fallback normalization
        return re.sub(r"[-_.]+", "-", s or "").lower()



SUGGESTED_LIBRARIES = [
    # Core & scientific
    "numpy","pandas","matplotlib","scipy","scikit-learn","sympy","numba","xarray",
    # DL/ML/AI
    "torch","torchvision","torchaudio","tensorflow","keras","jax","flax","transformers",
    "accelerate","diffusers","sentence-transformers","lightning","xgboost","catboost","lightgbm",
    # Data & viz
    "polars","seaborn","plotly","bokeh","altair","streamlit","dash",
    # NLP/CV/Audio utils
    "spacy","nltk","tesseract","pytesseract","opencv-python","mediapipe","paddleocr","librosa",
    # Web & APIs
    "fastapi","uvicorn","starlette","flask","requests","httpx","aiohttp","beautifulsoup4",
    # Dev & packaging
    "pytest","black","ruff","mypy","pydantic","typer","rich","loguru","pre-commit",
    # Data engineering
    "sqlalchemy","psycopg2-binary","pymongo","redis","duckdb","pyarrow","deltalake","great-expectations",
    # Jupyter
    "jupyter","ipykernel","notebook","jupyterlab",
]


class HadronProjectConfiguration(QWidget):
    def __init__(self, controller, hadron_designer, tab_widget):
        super().__init__()
        self.controller = controller
        self.tab_widget = tab_widget
        self.setStyleSheet("color: black;")

        # === Main Layout ===
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Section 1: Project Overview ===


        # --- Top bar: visible, clickable, right-aligned Save ---
        header = QWidget(self)
        header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        topbar = QHBoxLayout(header)
        topbar.setContentsMargins(0, 0, 0, 0)
        topbar.setSpacing(8)
        topbar.addStretch(1)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setEnabled(True)
        self.save_btn.setToolTip("Save project settings")
        self.save_btn.clicked.connect(lambda: self.save_project(
            name=self.name_input.text().strip(),
            project_type=self.type_combo.currentText()
        ))
        topbar.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(header)  # <- add the WIDGET, not just the layout

        overview_box = QGroupBox("📁 Project Overview")
        overview_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setText(controller.project.name) 
        self.name_input.setDisabled(True)
        overview_layout.addRow("Project Name:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Hadron", "Lepton"])
        self.type_combo.setCurrentText(controller.project.project_type)
        overview_layout.addRow("Project Type:", self.type_combo)

        overview_box.setLayout(overview_layout)
        main_layout.addWidget(overview_box)

       


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

        # --- Install New Package section above stays the same until here ---

        # Set up completer (backed by a QStringListModel)
        self.package_model = QStringListModel(self)
        self.package_model.setStringList(sorted(set(SUGGESTED_LIBRARIES)))

        self.package_completer = QCompleter(self.package_model, self)
        self.package_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.package_completer.setFilterMode(Qt.MatchFlag.MatchContains)            # match substrings
        self.package_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        self.package_search.setCompleter(self.package_completer)

       # Version completer + model
        self.SUGGESTED_VERSIONS=[]
        self.version_model = QStringListModel(self)
        self.version_model.setStringList(sorted(set(self.SUGGESTED_VERSIONS)))
        self.version_completer = QCompleter(self.version_model, self)
        self.version_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.version_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.version_input.setCompleter(self.version_completer)

        # Optional: debounce for lookups while typing
        self._ver_timer = QTimer(self); self._ver_timer.setSingleShot(True)
        self._ver_timer.timeout.connect(self._refresh_versions_for_current_package)
        self.package_search.textChanged.connect(lambda _t: self._ver_timer.start(250))

        # Also refresh immediately when a package is chosen from the package completer
        if hasattr(self, "package_completer"):
            self.package_completer.activated[str].connect(self._refresh_versions_for)

        popup_style = """
        QListView {
            background-color: white;
            color: black;
            selection-background-color: #0078d7; /* Windows blue highlight */
            selection-color: white;              /* text color when selected */
            border: 1px solid #888;
        }
        """

        self.package_completer.popup().setStyleSheet(popup_style)
        self.version_completer.popup().setStyleSheet(popup_style)


                        
        # --- Actions Row ---
        actions_row = QHBoxLayout()
        actions_row.setSpacing(20)  # extra spacing between buttons

        btn_style = """
        QPushButton {
            padding: 6px 14px;
            border: 2px solid #555;
            border-radius: 6px;
            background-color: #f9f9f9;
        }
        QPushButton:hover {
            background-color: #e6e6e6;
        }
        QPushButton:pressed {
            background-color: #dcdcdc;
        }
        """

        self.btn_load_req = QPushButton("📂 Load Requirements.txt")
        self.btn_load_req.setStyleSheet(btn_style)
        self.btn_load_req.clicked.connect(self.install_requirements_txt)

        self.btn_save_env = QPushButton("💾 Save Current Environment")
        self.btn_save_env.setStyleSheet(btn_style)
        self.btn_save_env.clicked.connect(self.save_environment)

        self.btn_wipe_env = QPushButton("🧨 Wipe Environment")
        self.btn_wipe_env.setStyleSheet(btn_style)
        self.btn_wipe_env.clicked.connect(self.wipe_environment)

        # Add with stretches so they spread evenly
        actions_row.addStretch(1)
        actions_row.addWidget(self.btn_load_req)
        actions_row.addStretch(1)
        actions_row.addWidget(self.btn_save_env)
        actions_row.addStretch(1)
        actions_row.addWidget(self.btn_wipe_env)
        actions_row.addStretch(1)

        main_layout.addLayout(actions_row)

    def _schedule_version_refresh(self, delay_ms: int = 250):
        # restart debounce timer
        self._ver_timer.start(delay_ms)

    def _refresh_versions_for_current_package(self):
        name = self.package_search.text().strip()
        if not name:
            self.version_model.setStringList([])
            return
        self._refresh_versions_for(name)

    def _refresh_versions_for(self, pkg_name: str):
        # call your endpoint that returns {"versions": [...]}
        def fetch():
            versions = []
            try:
                # === YOUR ENDPOINT HERE ===
                # Example: Simple API or your own proxy that returns {"versions": [...]}
                # resp = requests.get(f"https://<your-endpoint>/{pkg_name}", timeout=6)
                # For illustration, I'll use the Simple API JSON and *simulate* a 'versions' key:
                resp = requests.get(
                    f"https://pypi.org/simple/{pkg_name}/",
                    headers={"Accept": "application/vnd.pypi.simple.v1+json",
                            "User-Agent": "ProtoInstaller/1.0 (PyQt6)"},
                    timeout=6,
                )
                if resp.status_code == 200:
                    data = resp.json() or {}
                    # If your endpoint already returns {"versions": [...]}, do this:
                    versions = list(data.get("versions", []))

                    # If you’re actually using Simple API JSON (which gives "files"),
                    # you can keep your current extractor and then assign to `versions`.

                # Optional: sort newest-first (semantic if packaging is available)
                try:
                    from packaging.version import Version as _V
                    versions.sort(key=lambda v: _V(str(v)), reverse=True)
                except Exception:
                    versions.sort(reverse=True)

                # Cap list for UI sanity
                if len(versions) > 50:
                    versions = versions[:50]
                print(versions)

            except Exception:
                versions = []

            # Push to the completer model on the UI thread
            self.version_model.setStringList(sorted(set(versions)))
            

        threading.Thread(target=fetch, daemon=True).start()

    def clear_versions_if_blank(self, text: str):
        if not text.strip():
            self.version_model.setStringList([])


    def install_requirements_txt(self):
        # Pick a requirements.txt
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Install from requirements.txt",
            "",
            "Text files (*.txt);;All files (*.*)"
        )
        if not path:
            return

        # Confirm
        confirm = QMessageBox.question(
            self,
            "Install Dependencies",
            f"Install all dependencies listed in:\n{path} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        def run_install():
            # Mirror your install pattern (same python, capture, text)
            result = subprocess.run(
                [self.controller.project.python_path, "-m", "pip", "install", "-r", path],
                capture_output=True,
                text=True
            )

            def handle_result():
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", f"Installed dependencies from:\n{path}")
                else:
                    # Show stderr; pip often writes useful info there
                    QMessageBox.critical(self, "Error",
                                        f"Failed to install from requirements.txt:\n{result.stderr}")
                self.populate_installed_packages()

            QTimer.singleShot(0, handle_result)

        threading.Thread(target=run_install, daemon=True).start()


    def save_environment(self):
        # Pick where to save
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Current Environment (requirements.txt)",
            str(Path(self.controller.project.base_path) / "requirements.txt"),
            "Text files (*.txt);;All files (*.*)"
        )
        if not path:
            return

        def run():
            result = subprocess.run(
                [self.controller.project.python_path, "-m", "pip", "freeze"],
                capture_output=True,
                text=True
            )
            err = None
            if result.returncode == 0:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(result.stdout)
                except Exception as e:
                    err = str(e)

            def done():
                if result.returncode == 0 and not err:
                    QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to save requirements.txt:\n{err or result.stderr}")
            QTimer.singleShot(0, done)

        threading.Thread(target=run, daemon=True).start()


    def wipe_environment(self):
        confirm = QMessageBox.question(
            self,
            "Wipe Environment",
            "This will uninstall ALL packages except pip/setuptools/wheel.\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        pybin = self.controller.project.python_path

        def run():
            freeze = subprocess.run(
                [pybin, "-m", "pip", "freeze"],
                capture_output=True,
                text=True
            )
            if freeze.returncode != 0:
                code = 1
                out = freeze.stderr
            else:
                lines = [ln.strip() for ln in freeze.stdout.splitlines() if ln.strip()]
                pkgs = []
                for ln in lines:
                    # Ignore comments/editable lines/flags
                    if ln.startswith("#") or ln.startswith("-e ") or ln.startswith("-f ") or ln.startswith("--"):
                        continue
                    # Get bare package name (handle extras and various spec formats)
                    token = (ln.split(" @ ")[0]
                            .split("===")[0]
                            .split("==")[0]
                            .split(">=")[0]
                            .split("<=")[0]
                            .split("~=")[0]
                            .split(";")[0]
                            .strip())
                    token = token.split("[")[0].strip()  # drop extras like pkg[foo]
                    if token and token.lower() not in {"pip", "setuptools", "wheel"}:
                        pkgs.append(token)

                if pkgs:
                    chunks = [pkgs[i:i+80] for i in range(0, len(pkgs), 80)]
                    outs = []
                    code = 0
                    for chunk in chunks:
                        proc = subprocess.run(
                            [pybin, "-m", "pip", "uninstall", "-y", *chunk],
                            capture_output=True,
                            text=True
                        )
                        outs.append(proc.stdout if proc.returncode == 0 else proc.stderr)
                        if proc.returncode != 0:
                            code = proc.returncode
                            break
                    out = "\n".join(outs)
                else:
                    code = 0
                    out = "No third-party packages found."

            def done():
                if code == 0:
                    QMessageBox.information(self, "Environment Wiped",
                                            "All third-party packages have been uninstalled.\n" + out[:4000])
                else:
                    QMessageBox.critical(self, "Wipe Failed", out[:4000])
                self.populate_installed_packages()
            QTimer.singleShot(0, done)

        threading.Thread(target=run, daemon=True).start()

    def save_project(self, name, project_type):
        self.controller.project.name =  name
        self.controller.project.project_type = project_type
        self.controller.project.save()
        print('Project is saved')
        
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

        self.hadron_designer.start_project(
            name=name,
            path=path,
            entry_block=entry,
            runtime_target=runtime,
            project_type=project_type
        )

        
    def populate_installed_packages(self):
        print(self.controller)
        print(self.controller.project.python_path)
        self.package_table.setRowCount(0)
        try:
            result = subprocess.run(
                [self.controller.project.python_path, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            packages = json.loads(result.stdout)
            for pkg in packages:
                name = pkg['name']
                version = pkg['version']
                row = self.package_table.rowCount()
                self.package_table.insertRow(row)
                self.package_table.setItem(row, 0, QTableWidgetItem(name))
                self.package_table.setItem(row, 1, QTableWidgetItem(version))

        except Exception as e:
            print(e)
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
        name = self.package_search .text().strip()
        version = self.version_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Missing Package", "Please enter a package name.")
            return

        # Check if package is already installed
        installed_version = None
        for row in range(self.package_table.rowCount()):
            item = self.package_table.item(row, 0)
            if item and item.text().lower() == name.lower():
                installed_version = self.package_table.item(row, 1).text()
                break

        if installed_version:
            if not version or version == installed_version:
                QMessageBox.information(self, "Already Installed",
                    f"'{name}' is already installed with version {installed_version}. Skipping.")
                return
            else:
                msg = f"'{name}' is installed with version {installed_version}. Reinstall with version {version}?"
                confirm = QMessageBox.question(self, "Reinstall?", msg,
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if confirm != QMessageBox.StandardButton.Yes:
                    return

        # Compose package string
        package = f"{name}=={version}" if version else name

        def run_install():
            result = subprocess.run(
                [self.controller.project.python_path, "-m", "pip", "install", "--upgrade", package],
                capture_output=True,
                text=True
            )

            def handle_result():
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", f"Installed: {package}")
                else:
                    QMessageBox.critical(self, "Error", f"Failed to install:\n{result.stderr}")
                self.populate_installed_packages()

            QTimer.singleShot(0, handle_result)

        threading.Thread(target=run_install).start()
    
    
    def show_context_menu(self, position):
        index = self.package_table.indexAt(position)
        if not index.isValid():
            return

        row = index.row()
        package_name = self.package_table.item(row, 0).text()

        menu = QMenu()
        uninstall_action = menu.addAction(f"❌ Uninstall '{package_name}'")
        action = menu.exec(self.package_table.viewport().mapToGlobal(position))

        if action == uninstall_action:
            self.uninstall_package(package_name)

    def uninstall_package(self, package_name):
        confirm = QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to uninstall '{package_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            def run_uninstall():
                result = subprocess.run(
                    [self.controller.project.python_path, "-m", "pip", "uninstall", "-y", package_name],
                    capture_output=True,
                    text=True
                )

                def handle_result():
                    if result.returncode == 0:
                        QMessageBox.information(self, "Uninstalled", f"Successfully uninstalled: {package_name}")
                    else:
                        QMessageBox.critical(self, "Error", f"Failed to uninstall:\n{result.stderr}")
                    self.populate_installed_packages()

                QTimer.singleShot(0, handle_result)

            threading.Thread(target=run_uninstall).start()

