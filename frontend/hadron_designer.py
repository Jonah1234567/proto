from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMainWindow, QTabWidget, QMenuBar, QMenu, QFileDialog, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QAction

from canvas import Canvas
from block_library_dialog import BlockLibraryDialog
from hadron_project_configuration import HadronProjectConfiguration
from components.file_sidebar import FileSidebar
from PyQt6.QtGui import QShortcut, QKeySequence

import sys
import os
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
        self.open_file_tabs = {}  # maps file paths to tab widgets


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

        self.config_tab = HadronProjectConfiguration(controller=self.controller, hadron_designer=self, tab_widget=self.tabs)
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

        from PyQt6.QtWidgets import QFrame, QStackedLayout

        # === Terminal Container with Overlay Button ===
        terminal_container = QFrame()
        terminal_container.setFixedHeight(150)
        terminal_container.setStyleSheet("background-color: transparent;")

        # Absolute layout for overlap
        terminal_layout = QStackedLayout(terminal_container)
        terminal_layout.setContentsMargins(0, 0, 0, 0)

        # Output Box
        self.output_box = QTextEdit(terminal_container)
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                color: black;
                font-family: monospace;
                border: 2px solid black;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                border: none;
                background: #eee;
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QScrollBar:horizontal {
                border: none;
                background: #eee;
                height: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #888;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
                subcontrol-origin: margin;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        terminal_layout.addWidget(self.output_box)


        # Clear Button
        self.clear_button = QPushButton("🧹 Clear", terminal_container)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: 1px solid black;
                border-radius: 4px;
                font-size: 11px;
                padding: 2px 6px;
            }
        """)
        self.clear_button.setFixedSize(60, 24)
        self.clear_button.clicked.connect(self.clear_output_box)
        

        def reposition_clear_button():
            self.clear_button.move(terminal_container.width() - 72, 5)

        terminal_container.resizeEvent = lambda event: reposition_clear_button()
        reposition_clear_button()  # run once initially


        # Add terminal to layout
        editor_area.addWidget(terminal_container)



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

        terminal_visible = self.controller.project.open_terminal
        self.output_box.setVisible(terminal_visible)
        self.clear_button.setVisible(terminal_visible)
        self.toggle_terminal_action.setChecked(terminal_visible)


        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_current_tab)

        try:
            with open("./frontend/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print("Could not load stylesheet:", e)

    def create_canvas(self, set_as_main=False):
        canvas = Canvas(self.tabs, self.controller)
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
        filepath = str(Path(filepath).resolve())

        # Check if this file is already open
        if filepath in self.open_file_tabs:
            existing_tab = self.open_file_tabs[filepath]
            self.tabs.setCurrentWidget(existing_tab)
            print(f"📄 File already open: {filepath}")
            return

        file_name = Path(filepath).name
        canvas, tab_widget = self.create_canvas(True)
        canvas.filepath = filepath

        canvas.load_layout(filepath)
        canvas.modified.connect(lambda: self.mark_canvas_tab_modified(canvas))

        self.canvas_tabs[tab_widget] = canvas
        self.open_file_tabs[filepath] = tab_widget

        conflicts = [f for f in self.open_file_tabs if Path(f).name == file_name and f != filepath]
        if conflicts:
            rel_path = str(Path(filepath).relative_to(self.controller.project.base_path))
            tab_label = f"📄 {rel_path.replace(os.sep, '/')}"
        else:
            tab_label = f"📄 {file_name}"


        self.tabs.addTab(tab_widget, tab_label)
        self.tabs.setCurrentWidget(tab_widget)
        self.on_tab_changed(self.tabs.currentIndex())



    def clear_output_box(self):
        self.output_box.clear()

    def run_blocks(self):
        canvas = self.get_current_canvas()
        if canvas is None:
            print("❌ No canvas found for current tab.")
            return
        print(f"▶ Executing all blocks for canvas: {canvas.filepath}")
        run_all_blocks(self, canvas)


    def save_layout_prompt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Layout", "", "JSON Files (*.json)")
        if path:
            self.canvas.save_layout(path)

    def load_layout_prompt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Layout", "", "JSON Files (*.json)")
        if path:
            self.canvas.load_layout(path)


    def close_tab(self, index):
        widget = self.tabs.widget(index)

        # Check if this is a canvas tab and has unsaved changes
        canvas = self.canvas_tabs.get(widget)
        if canvas:
            current_text = self.tabs.tabText(index)
            if current_text.endswith("*"):
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Unsaved Changes")
                msg_box.setText(f"Do you want to save changes to '{current_text[:-2]}'?")
                msg_box.setIcon(QMessageBox.Icon.Question)
                msg_box.setStandardButtons(
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel
                )
                msg_box.setDefaultButton(QMessageBox.StandardButton.Save)
                msg_box.setStyleSheet("""
                    QMessageBox {
                        color: black;
                        font-size: 14px;
                    }
                    QPushButton {
                        color: black;
                    }
                """)
                response = msg_box.exec()

                if response == QMessageBox.StandardButton.Save:
                    self.tabs.setCurrentIndex(index)
                    self.save_current_tab()
                elif response == QMessageBox.StandardButton.Cancel:
                    return

            # Remove from tracking dicts
            self.canvas_tabs.pop(widget)
            if hasattr(canvas, "filepath") and canvas.filepath:
                filepath = str(Path(canvas.filepath).resolve())
                self.open_file_tabs.pop(filepath, None)

        elif hasattr(widget, "save_changes"):
            # Handle editors like block editors (if needed)
            current_text = self.tabs.tabText(index)
            if current_text.endswith("*"):
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Unsaved Changes")
                msg_box.setText(f"Do you want to save changes to '{current_text[:-2]}'?")
                msg_box.setIcon(QMessageBox.Icon.Question)
                msg_box.setStandardButtons(
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel
                )
                msg_box.setDefaultButton(QMessageBox.StandardButton.Save)
                msg_box.setStyleSheet("""
                    QMessageBox {
                        color: black;
                        font-size: 14px;
                    }
                    QPushButton {
                        color: black;
                    }
                """)
                response = msg_box.exec()

                if response == QMessageBox.StandardButton.Save:
                    self.tabs.setCurrentIndex(index)
                    self.save_current_tab()
                elif response == QMessageBox.StandardButton.Cancel:
                    return

        self.tabs.removeTab(index)


    def save_editor_tab(self, index):
        editor_widget = self.tabs.widget(index)
        if hasattr(editor_widget, "save_changes"):
            editor_widget.save_changes()

    def on_tab_changed(self, index):
        current_widget = self.tabs.widget(index)
        canvas = self.canvas_tabs.get(current_widget)
    
    def get_current_canvas(self):
        current_tab = self.tabs.currentWidget()
        return self.canvas_tabs.get(current_tab, None)


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
        self.clear_button.setVisible(not visible)  # Add this line
        self.toggle_terminal_action.setChecked(not visible)

    def mark_canvas_tab_modified(self, canvas):
        for tab, tracked_canvas in self.canvas_tabs.items():
            if tracked_canvas == canvas:
                index = self.tabs.indexOf(tab)
                current_text = self.tabs.tabText(index)
                if not current_text.endswith("*"):
                    self.tabs.setTabText(index, current_text + " *")
                break

    
    
    def save_current_tab(self):
        current_tab = self.tabs.currentWidget()
        print(f"🔍 Current tab widget: {current_tab}")

        # === Case 1: Canvas Tab ===
        canvas = self.canvas_tabs.get(current_tab)
        if canvas:
            if hasattr(canvas, "filepath") and canvas.filepath:
                canvas.save_layout(canvas.filepath)
                print(f"✅ Saved to {canvas.filepath}")
            else:
                from PyQt6.QtWidgets import QFileDialog
                path, _ = QFileDialog.getSaveFileName(
                    self, "Save Canvas Layout", "", "Quark Files (*.quark)"
                )
                if path:
                    canvas.filepath = path
                    canvas.save_layout(path)
                    print(f"💾 Saved as new file: {path}")

        # === Case 2: Block Editor Tab (any tab with save_changes method)
        elif hasattr(current_tab, "save_changes") and callable(current_tab.save_changes):
            try:
                current_tab.save_changes()
                print("💾 Saved block editor tab.")
            except Exception as e:
                print(f"❌ Error saving block editor tab: {e}")

        # === Unknown Tab Type
        else:
            print("❌ Unrecognized tab type. Nothing was saved.")
            return

        # === Remove asterisk from the tab title
        tab_index = self.tabs.indexOf(current_tab)
        current_label = self.tabs.tabText(tab_index)
        self.controller.project.save()
        if current_label.endswith("*"):
            self.tabs.setTabText(tab_index, current_label[:-1])








