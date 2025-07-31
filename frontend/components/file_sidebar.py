from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeView, QPushButton, QLineEdit, QMessageBox
)
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QDir, pyqtSignal, QItemSelectionModel
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMenu, QMessageBox, QInputDialog


class FileSidebar(QWidget):
    file_open_requested = pyqtSignal(str)

    def __init__(self, start_path: str, parent=None):
        super().__init__(parent)
        self.start_path = Path(start_path)
        self.selected_path = self.start_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # === Title ===
        title = QLabel("📁 File Explorer")
        title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                padding: 4px;
                color: black;
            }
        """)
        layout.addWidget(title)

        # === Filename input ===
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("New file name...")
        self.filename_input.setVisible(False)
        self.filename_input.setStyleSheet("""
            QLineEdit {
                font-size: 12px;
                padding: 4px;
                border: 1px solid #aaa;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
        """)
        self.filename_input.returnPressed.connect(self.create_new_file)
        layout.addWidget(self.filename_input)

        self.add_file_button = QPushButton("➕ New File")
        self.add_file_button.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                padding: 4px 8px;
                color: black;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f8f8;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.add_file_button.clicked.connect(self.show_filename_input)
        layout.addWidget(self.add_file_button)

        # === Tree ===
        self.model = QFileSystemModel()
        self.model.setReadOnly(False)

        self.model.setRootPath(str(self.start_path))
        self.model.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot | QDir.Filter.Files
        )

        self.tree = QTreeView()
        self.tree.setModel(self.model)

        self.tree.setEditTriggers(
            QTreeView.EditTrigger.SelectedClicked |
            QTreeView.EditTrigger.EditKeyPressed |
            QTreeView.EditTrigger.AnyKeyPressed
        )

        self.tree.setRootIndex(self.model.index(str(self.start_path)))
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tree.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QTreeView.DragDropMode.InternalMove)


        # ✅ Apply selection style override
        self.tree.setStyleSheet("""
            QTreeView {
                color: black;
                background-color: white;
                font-size: 13px;
            }

            QTreeView::item:selected {
                background-color: #5dade2;
                color: black;
            }

            QTreeView::item:selected:active {
                background-color: #3498db;
            }

            QTreeView::item:selected:!active {
                background-color: #aed6f1;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #b0bec5;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
            QTreeView QLineEdit {
                color: black;
                background-color: white;
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 2px;
            }
        """)

        layout.addWidget(self.tree)

        # === Connections ===
        self.tree.selectionModel().selectionChanged.connect(self.on_item_selected)
        self.tree.doubleClicked.connect(self.on_file_double_clicked)

        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)

        # Enable inline editing
        self.tree.setEditTriggers(QTreeView.EditTrigger.SelectedClicked)

    def show_filename_input(self):
        self.filename_input.setVisible(True)
        self.filename_input.setFocus()

    def create_new_file(self):
        filename = self.filename_input.text().strip()
        self.filename_input.clear()
        self.filename_input.setVisible(False)

        if not filename:
            return

        if not filename.endswith(".quark"):
            filename += ".quark"

        folder_path = Path(self.selected_path)
        file_path = folder_path / filename

        if file_path.exists():
            QMessageBox.warning(self, "File Exists", "A file with this name already exists.")
            return

        try:
            file_path.write_text("")  # create blank file

            # Ensure tree refresh and selection
            index = self.model.index(str(file_path))
            self.tree.scrollTo(index)
            self.tree.setCurrentIndex(index)
            self.tree.selectionModel().select(
                index,
                QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows
            )
            self.file_open_requested.emit(str(file_path))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create file:\n{e}")

    def on_file_double_clicked(self, index):
        path = self.model.filePath(index)
        if path.endswith(".quark"):
            self.file_open_requested.emit(path)

    def on_item_selected(self, selected, deselected):
        indexes = selected.indexes()
        if indexes:
            index = indexes[0]
            path = Path(self.model.filePath(index))
            if self.model.isDir(index):
                self.selected_path = str(path)
            else:
                self.selected_path = str(path.parent)

    def open_context_menu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #000;
                color: white;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 12px;
            }
            QMenu::item:selected {
                background-color: #333;
            }
        """)

        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")

        action = menu.exec(self.tree.viewport().mapToGlobal(position))

        if action == rename_action:
            self.tree.edit(index)  # This works only if readOnly is False
        elif action == delete_action:
            path = self.model.filePath(index)
            try:
                if Path(path).is_file():
                    Path(path).unlink()
                elif Path(path).is_dir():
                    shutil.rmtree(path)

                # Force refresh
                self.model.setRootPath("")
                self.model.setRootPath(str(self.start_path))

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{e}")
