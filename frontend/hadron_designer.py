from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMainWindow, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMenuBar, QMenu, QFileDialog
from PyQt6.QtGui import QTextCursor
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QTextEdit

from canvas import Canvas
from block_library_dialog import BlockLibraryDialog
import os

import sys
from pathlib import Path
from hadron_project_configuration import HadronProjectConfiguration

from components.file_sidebar import FileSidebar

sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.engine import run_all_blocks
from backend.saving import save_to_template
from backend.loading import load_file

class HadronDesignerWindow(QMainWindow):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        

             # === Menu Bar ===
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        save_action = QAction("Save Layout", self)
        save_action.triggered.connect(self.save_layout_prompt)
        file_menu.addAction(save_action)

        load_action = QAction("Load Layout", self)
        load_action.triggered.connect(self.load_layout_prompt)
        file_menu.addAction(load_action)

       # === Main vertical layout ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # === Title bar ===
        title = QLabel("Proto")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title)

        # === Horizontal layout: Sidebar + Editor Content ===
        content_row = QHBoxLayout()

        # === Sidebar on the left ===
        print(self.controller.project.base_path)
        sidebar = FileSidebar(str(self.controller.project.base_path))
        sidebar.setFixedWidth(240)
        sidebar.file_open_requested.connect(self.open_quark_file)
        content_row.addWidget(sidebar)

        # === Right side layout for tabs + buttons + output ===
        editor_area = QVBoxLayout()

        # === Editor Tabs ===
        self.tabs = QTabWidget()
        self.tabs.setTabBarAutoHide(False)
        editor_area.addWidget(self.tabs)

        # Canvas tab
        canvas_tab = QWidget()
        canvas_layout = QVBoxLayout(canvas_tab)
        self.canvas = Canvas(self.tabs)
        canvas_layout.addWidget(self.canvas)

        # Config tab
        self.config_tab = HadronProjectConfiguration(controller=self, tab_widget=self.tabs)
        self.tabs.addTab(self.config_tab, "🛠 Project Config")
        self.tabs.setCurrentWidget(self.config_tab)

        self.tabs.setStyleSheet("QTabBar::tab { color: black; }")
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # === Bottom Buttons ===
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.add_block_menu = QMenu(self)
        self.add_block_menu.addAction("➕ Add Blank Block", self.canvas.add_block)
        self.add_block_menu.addAction("📦 Import From Library", self.import_from_library)
        self.add_block_menu.addAction("🔣 Add Variable Block", self.canvas.add_variable_block)
        self.add_block_menu.addAction("🔀 Add Conditional Block", self.canvas.add_conditional_block)
        self.add_block_menu.addAction("🔁 Add Loop Block", self.canvas.add_loop_block)

        self.add_block_button = QPushButton("➕ Add Block")
        self.add_block_button.setFixedWidth(200)
        self.add_block_button.setStyleSheet("""
            font-size: 16px;
            padding: 10px;
            color: black;
            border: 2px solid black;
            border-radius: 8px;
        """)
        self.add_block_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_block_button.clicked.connect(lambda: self.canvas.add_block())
        self.add_block_button.installEventFilter(self)

        self.run_button = QPushButton("▶ Run")
        self.run_button.setFixedWidth(200)
        self.run_button.setStyleSheet("""
            font-size: 16px;
            padding: 10px;
            color: black;
            border: 2px solid black;
            border-radius: 8px;
        """)
        self.run_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_button.clicked.connect(self.run_blocks)

        bottom_row.addWidget(self.run_button)
        bottom_row.addWidget(self.add_block_button)
        bottom_row.setContentsMargins(0, 10, 10, 10)
        editor_area.addLayout(bottom_row)

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

        # Add right editor area to horizontal layout
        content_row.addLayout(editor_area)

        # Add the horizontal content row to the main vertical layout
        main_layout.addLayout(content_row)

        # Optional: load stylesheet
        try:
            with open("./frontend/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print("Could not load stylesheet:", e)


    def redirector(self, inputStr):
            self.output_box.moveCursor(QTextCursor.MoveOperation.End)
            self.output_box.insertPlainText(inputStr)
        
    def append_output(self, text):
        self.output_box.moveCursor(self.output_box.textCursor().End)
        self.output_box.insertPlainText(text)


    def on_tab_changed(self, index):
        tab_name = self.tabs.tabText(index)
        if tab_name == "Canvas":
            self.add_block_button.setText("➕ Add Block")
            self.add_block_button.clicked.disconnect()
            self.add_block_button.clicked.connect(self.canvas.add_block)
        else:
            self.add_block_button.setText("💾 Save")
            self.add_block_button.clicked.disconnect()
            self.add_block_button.clicked.connect(lambda: self.save_editor_tab(index))

    def save_editor_tab(self, index):
        editor_widget = self.tabs.widget(index)
        if hasattr(editor_widget, "save_changes"):
            editor_widget.save_changes()
    def close_tab(self, index):
        # Prevent canvas tab from being closed
        if self.tabs.tabText(index) == "Canvas":
            return
        self.tabs.removeTab(index)

    def save_layout_prompt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Layout", "", "JSON Files (*.json)")
        if path:
            self.canvas.save_layout(path)

    def load_layout_prompt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Layout", "", "JSON Files (*.json)")
        if path:
            self.canvas.load_layout(path)

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
    
    def import_from_library(self):
        dialog = BlockLibraryDialog("block_libraries", self)
        if dialog.exec():
            template = dialog.get_selected_template()
            if template:
                print('firing')
                self.canvas.load_block_from_template_wrapper(template)

    def eventFilter(self, source, event):
        if source == self.add_block_button and event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton:
                self.add_block_menu.exec(self.add_block_button.mapToGlobal(event.position().toPoint()))
                return True  # Don't pass event on
        return super().eventFilter(source, event)

    def open_quark_file(self, path: str):
        file_name = Path(path).name
        new_canvas = Canvas(self.tabs)
        new_canvas.load_layout(path)
        self.tabs.addTab(new_canvas, f"📄 {file_name}")
        self.tabs.setCurrentWidget(new_canvas)