from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMainWindow, QTabWidget, QMenuBar, QMenu, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QAction

from canvas import Canvas
from block_library_dialog import BlockLibraryDialog
from hadron_project_configuration import HadronProjectConfiguration
from components.file_sidebar import FileSidebar

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.engine import run_all_blocks
from backend.saving import save_to_template
from backend.loading import load_file

class HadronDesignerWindow(QMainWindow):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.canvas_tabs = {}

        # === Menu Bar ===
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        save_action = QAction("Save Layout", self)
        save_action.triggered.connect(self.save_layout_prompt)
        file_menu.addAction(save_action)

        load_action = QAction("Load Layout", self)
        load_action.triggered.connect(self.load_layout_prompt)
        file_menu.addAction(load_action)

        # === Main Layout ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        title = QLabel("Proto")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title)

        content_row = QHBoxLayout()

        # === Sidebar ===
        sidebar = FileSidebar(str(self.controller.project.base_path))
        sidebar.setFixedWidth(240)
        sidebar.file_open_requested.connect(self.open_quark_file)
        content_row.addWidget(sidebar)

        # === Editor Area ===
        editor_area = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.setTabBarAutoHide(False)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.tabs.setStyleSheet("QTabBar::tab { color: black; }")

        self.config_tab = HadronProjectConfiguration(controller=self, tab_widget=self.tabs)
        self.tabs.addTab(self.config_tab, "🛠 Project Config")
        self.tabs.setCurrentWidget(self.config_tab)

        editor_area.addWidget(self.tabs)

        # === Bottom Buttons ===
        self.add_block_button = None
        self.run_button = None
        self.add_block_menu = None

        self.bottom_row = QHBoxLayout()
        self.bottom_row.addStretch()
        self.bottom_row.setContentsMargins(0, 10, 10, 10)
        editor_area.addLayout(self.bottom_row)

        # === Output Box ===
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                color: black;
                font-family: monospace;
                border: 2px solid black;
                border-radius: 6px;
            }
        """)
        self.output_box.setFixedHeight(150)
        editor_area.addWidget(self.output_box)

        content_row.addLayout(editor_area)
        main_layout.addLayout(content_row)

                # === Utilities Menu ===
        utilities_menu = menu_bar.addMenu("Utilities")

        toggle_terminal_action = QAction("Toggle Terminal", self)
        toggle_terminal_action.setCheckable(True)
        toggle_terminal_action.setChecked(True)
        toggle_terminal_action.triggered.connect(self.toggle_terminal_visibility)
        utilities_menu.addAction(toggle_terminal_action)

        self.toggle_terminal_action = toggle_terminal_action

        self.output_box.setVisible(self.controller.project.open_terminal)
        self.toggle_terminal_action.setChecked(self.controller.project.open_terminal)

        try:
            with open("./frontend/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print("Could not load stylesheet:", e)

    def create_canvas(self, set_as_main=False):
        canvas = Canvas(self.tabs)
        canvas_tab = QWidget()
        layout = QVBoxLayout(canvas_tab)
        layout.addWidget(canvas)
        layout.setContentsMargins(0, 0, 0, 0)

        if set_as_main:
            self.canvas = canvas

            # === Clean up previous buttons ===
            if self.add_block_button is not None:
                self.bottom_row.removeWidget(self.add_block_button)
                self.add_block_button.deleteLater()
                self.add_block_button = None

            if self.run_button is not None:
                self.bottom_row.removeWidget(self.run_button)
                self.run_button.deleteLater()
                self.run_button = None

            # === Create new menu and buttons ===
            self.add_block_menu = QMenu(self)
            self.add_block_menu.addAction("➕ Add Blank Block", canvas.add_block)
            self.add_block_menu.addAction("📦 Import From Library", self.import_from_library)
            self.add_block_menu.addAction("🔣 Add Variable Block", canvas.add_variable_block)
            self.add_block_menu.addAction("🔀 Add Conditional Block", canvas.add_conditional_block)
            self.add_block_menu.addAction("🔁 Add Loop Block", canvas.add_loop_block)

            self.add_block_button = QPushButton("➕ Add Block")
            self.add_block_button.setFixedWidth(200)
            self.add_block_button.setStyleSheet("font-size: 16px; padding: 10px; color: black; border: 2px solid black; border-radius: 8px;")
            self.add_block_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.add_block_button.clicked.connect(canvas.add_block)
            self.add_block_button.installEventFilter(self)

            self.run_button = QPushButton("▶ Run")
            self.run_button.setFixedWidth(200)
            self.run_button.setStyleSheet("font-size: 16px; padding: 10px; color: black; border: 2px solid black; border-radius: 8px;")
            self.run_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.run_button.clicked.connect(self.run_blocks)

            self.bottom_row.addWidget(self.run_button)
            self.bottom_row.addWidget(self.add_block_button)

        return canvas, canvas_tab

    def open_quark_file(self, filepath):
        file_name = Path(filepath).name
        canvas, tab_widget = self.create_canvas(True)

        # Load content into canvas
        canvas.load_layout(filepath)

        # Track the canvas for the tab
        self.canvas_tabs[tab_widget] = canvas

        # Add tab and switch to it
        self.tabs.addTab(tab_widget, f"📄 {file_name}")
        self.tabs.setCurrentWidget(tab_widget)

        # === Manually trigger tab change logic to update button connections ===
        self.on_tab_changed(self.tabs.currentIndex())


    def run_blocks(self):
        print("▶ Executing all blocks...")
        run_all_blocks(self, self.canvas)

    def save_layout_prompt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Layout", "", "JSON Files (*.json)")
        if path:
            self.canvas.save_layout(path)

    def load_layout_prompt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Layout", "", "JSON Files (*.json)")
        if path:
            self.canvas.load_layout(path)

    def close_tab(self, index):
        if self.tabs.tabText(index) == "Canvas":
            return
        self.tabs.removeTab(index)

    def save_editor_tab(self, index):
        editor_widget = self.tabs.widget(index)
        if hasattr(editor_widget, "save_changes"):
            editor_widget.save_changes()

    def on_tab_changed(self, index):
        current_widget = self.tabs.widget(index)
        canvas = self.canvas_tabs.get(current_widget)

        # Safely check if buttons exist and are not None
        has_buttons = all(
            hasattr(self, name) and getattr(self, name) is not None
            for name in ["add_block_button", "run_button", "add_block_menu"]
        )

        if canvas and has_buttons:
            self.add_block_button.setText("➕ Add Block")
            self.add_block_button.clicked.disconnect()
            self.add_block_button.clicked.connect(lambda: canvas.add_block("Untitled Block"))

            self.run_button.clicked.disconnect()
            self.run_button.clicked.connect(lambda: run_all_blocks(self, canvas))

            self.add_block_menu.clear()
            self.add_block_menu.addAction("➕ Add Blank Block", canvas.add_block)
            self.add_block_menu.addAction("📦 Import From Library", self.import_from_library)
            self.add_block_menu.addAction("🔣 Add Variable Block", canvas.add_variable_block)
            self.add_block_menu.addAction("🔀 Add Conditional Block", canvas.add_conditional_block)
            self.add_block_menu.addAction("🔁 Add Loop Block", canvas.add_loop_block)

        elif has_buttons:
            self.add_block_button.setText("💾 Save")
            self.add_block_button.clicked.disconnect()
            self.add_block_button.clicked.connect(lambda: self.save_editor_tab(index))



    def import_from_library(self):
        dialog = BlockLibraryDialog("block_libraries", self)
        if dialog.exec():
            template = dialog.get_selected_template()
            if template:
                self.canvas.load_block_from_template_wrapper(template)

    def append_output(self, text):
        self.output_box.moveCursor(QTextCursor.MoveOperation.End)
        self.output_box.insertPlainText(text)

    def redirector(self, inputStr):
        self.output_box.moveCursor(QTextCursor.MoveOperation.End)
        self.output_box.insertPlainText(inputStr)

    def eventFilter(self, source, event):
        if self.add_block_button and source == self.add_block_button and event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton:
                self.add_block_menu.exec(self.add_block_button.mapToGlobal(event.position().toPoint()))
                return True
        return super().eventFilter(source, event)
    
    def toggle_terminal_visibility(self):
        self.controller.project.open_terminal = not self.controller.project.open_terminal
        visible = self.output_box.isVisible()
        self.output_box.setVisible(not visible)
        self.toggle_terminal_action.setChecked(not visible)



