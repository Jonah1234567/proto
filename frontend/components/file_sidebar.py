from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeView
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QDir
from PyQt6.QtCore import pyqtSignal


class FileSidebar(QWidget):
    file_open_requested = pyqtSignal(str) 
    def __init__(self, start_path: str, parent=None):
        super().__init__(parent)

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

        # === File System Tree ===
        self.model = QFileSystemModel()
        self.model.setRootPath(start_path)
        self.model.setFilter(
            QDir.Filter.AllDirs |
            QDir.Filter.NoDotAndDotDot |
            QDir.Filter.Files
        )

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(start_path))
        self.tree.setColumnHidden(1, True)  # Size
        self.tree.setColumnHidden(2, True)  # File type
        self.tree.setColumnHidden(3, True)  # Last modified

        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)

        self.tree.setStyleSheet("""
            QTreeView {
                color: black;
                background-color: white;
                selection-background-color: #d6eaf8;
                selection-color: black;
                font-size: 13px;
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
        """)

        layout.addWidget(self.tree)
        self.tree.doubleClicked.connect(self.on_file_double_clicked)

    def on_file_double_clicked(self, index):
        path = self.model.filePath(index)
        if path.endswith(".quark"):
            self.file_open_requested.emit(path)
