from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QScrollArea, QWidget, QGridLayout,
    QPushButton, QLabel, QStackedLayout, QSpacerItem, QSizePolicy, QLineEdit
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
import os, json

class FolderCard(QWidget):
    def __init__(self, folder_name, icon_path, on_click):
        super().__init__()
        self.setFixedSize(100, 120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap(icon_path).scaled(
            64, 64,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        icon = QLabel()
        icon.setPixmap(pixmap)
        icon.setFixedSize(72, 72)
        icon.setStyleSheet("""
            border: 2px solid #2f3640;
            border-radius: 6px;
        """)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(folder_name)
        label.setStyleSheet("color: black; font-weight: bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon)
        layout.addWidget(label)

        # Add click behavior
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = lambda event: on_click()

class BlockLibraryDialog(QDialog):
    def __init__(self, library_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📚 Block Library")
        self.setMinimumSize(800, 647)
        self.library_path = library_path
        self.selected_template = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Title ===
        title = QLabel("Libraries Available")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: black; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title)

        # === Page stack
        self.stacked_layout = QStackedLayout()
        self.main_layout.addLayout(self.stacked_layout)

        # === Folder page ===
        self.folder_widget = QWidget()
        self.folder_main_layout = QVBoxLayout(self.folder_widget)  # vertical layout
        self.folder_main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Search bar
        self.library_search_bar = QLineEdit()
        self.library_search_bar.setPlaceholderText("🔍 Search libraries...")
        self.library_search_bar.setStyleSheet("padding: 6px; font-size: 14px; color: black;")
        self.library_search_bar.textChanged.connect(self.filter_libraries)
        self.folder_main_layout.addWidget(self.library_search_bar)

        # Grid layout inside the vertical layout
        self.folder_layout = QGridLayout()
        self.folder_layout.setSpacing(20)
        self.folder_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.folder_main_layout.addLayout(self.folder_layout)

        # Scroll area wrapping the folder widget
        self.folder_scroll = QScrollArea()
        self.folder_scroll.setWidgetResizable(True)
        self.folder_scroll.setWidget(self.folder_widget)

        # Add to stacked layout
        self.stacked_layout.addWidget(self.folder_scroll)


        # === Block list
        self.block_list_widget = QWidget()
        self.block_list_layout = QVBoxLayout(self.block_list_widget)
        self.block_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stacked_layout.addWidget(self.block_list_widget)

        self.load_folders()

    def load_folders(self):
        row, col = 1, 0
        self.library_widgets = []

        for folder in sorted(os.listdir(self.library_path)):
            folder_path = os.path.join(self.library_path, folder)
            icon_path = os.path.join(folder_path, "icon.png")

            if os.path.isdir(folder_path):
                btn = QPushButton()
                btn.setFixedSize(120, 120)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda _, p=folder_path: self.load_blocks(p))

                pixmap = QPixmap(icon_path) if os.path.exists(icon_path) else QPixmap(100, 100)
                btn.setIcon(QIcon(pixmap))
                btn.setIconSize(btn.size())
                btn.setStyleSheet("border: 2px solid black;")

                label = QLabel(folder)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("color: black; font-weight: normal;")

                box = QVBoxLayout()
                box_widget = QWidget()
                box_widget.setLayout(box)  # ✅ this is correct
                box.addWidget(btn)
                box.addWidget(label)
                box_widget.setLayout(box)

                self.folder_layout.addWidget(box_widget, row, col)
                self.library_widgets.append((box_widget, folder.lower()))

                col += 1
                if col >= 4:
                    col = 0
                    row += 1




    def load_blocks(self, folder_path):
        # Clear layout
        for i in reversed(range(self.block_list_layout.count())):
            widget = self.block_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # === Search bar ===
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search blocks or folders...")
        self.search_bar.setStyleSheet("padding: 6px; font-size: 14px; color: black;")
        self.search_bar.textChanged.connect(self.filter_blocks)
        self.block_list_layout.addWidget(self.search_bar)

        blocks_dir = os.path.join(folder_path, "blocks")
        if not os.path.exists(blocks_dir):
            print(f"❌ Missing folder: {blocks_dir}")
            return

        self.block_widgets = []  # Store for filtering
        found_any = False

        for item in sorted(os.listdir(blocks_dir)):
            item_path = os.path.join(blocks_dir, item)

            # Case 1: JSON block file
            if os.path.isfile(item_path) and item.endswith(".json"):
                try:
                    with open(item_path, "r") as f:
                        template = json.load(f)
                        name = template.get("name", item.replace(".json", ""))
                        btn = QPushButton(f"📄 {name}")
                        btn.setStyleSheet("text-align: left; color: black;")
                        btn.clicked.connect(lambda _, t=template: self.select_template(t))
                        self.block_list_layout.addWidget(btn)
                        self.block_widgets.append((btn, name.lower()))
                        found_any = True
                except Exception as e:
                    print(f"⚠️ Failed to load block: {item_path} — {e}")

            # Case 2: Folder (click to navigate deeper)
            elif os.path.isdir(item_path):
                folder_button = QPushButton(f"📁 {item}")
                folder_button.setStyleSheet("""
                    font-weight: bold;
                    color: black;
                    padding: 6px;
                    text-align: left;
                """)
                folder_button.clicked.connect(lambda _, p=item_path: self.show_blocks_in_folder(p))
                self.block_list_layout.addWidget(folder_button)
                self.block_widgets.append((folder_button, item.lower()))
                found_any = True

        if not found_any:
            msg = QLabel("No blocks or folders found.")
            msg.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
            self.block_list_layout.addWidget(msg)

        # Spacer and back button
        self.block_list_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        back_btn = QPushButton("⬅ Back")
        back_btn.setStyleSheet("""
            font-size: 14px;
            color: black;
            border: 2px solid black;
            border-radius: 6px;
            padding: 6px 12px;
        """)
        back_btn.clicked.connect(self.show_folder_grid)
        self.block_list_layout.addWidget(back_btn)

        self.stacked_layout.setCurrentWidget(self.block_list_widget)







    def show_folder_grid(self):
        # Clear layout
        for i in reversed(range(self.folder_grid_layout.count())):
            widget = self.folder_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # === Search bar ===
        self.library_search_bar = QLineEdit()
        self.library_search_bar.setPlaceholderText("🔍 Search libraries...")
        self.library_search_bar.setStyleSheet("padding: 6px; font-size: 14px; color: black;")
        self.library_search_bar.textChanged.connect(self.filter_libraries)
        self.folder_grid_layout.addWidget(self.library_search_bar, 0, 0, 1, 3)  # Full row


    def select_template(self, template):
        self.selected_template = template
        self.accept()

    def get_selected_template(self):
        return self.selected_template
    
    def _add_block_button(self, template):
        name = template.get("name", "Unnamed")
        btn = QPushButton(f"📦 {name}")
        btn.setStyleSheet("""
            font-weight: normal;
            color: black;
            text-align: left;
            padding: 6px;
        """)
        btn.clicked.connect(lambda _, t=template: self.select_template(t))
        self.block_list_layout.addWidget(btn)

    def show_blocks_in_folder(self, folder_path):
        # Reuse load_blocks logic on subfolder
        self.load_blocks(folder_path)

    def filter_blocks(self, text):
        query = text.lower().strip()
        for widget, label in self.block_widgets:
            widget.setVisible(query in label)

    def filter_libraries(self, text):
        query = text.lower().strip()

        # Clear current grid layout
        for i in reversed(range(self.folder_layout.count())):
            widget = self.folder_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Re-add only matching widgets, 4 columns per row
        row, col = 0, 0
        for widget, label in self.library_widgets:
            if query in label:
                self.folder_layout.addWidget(widget, row, col)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1




