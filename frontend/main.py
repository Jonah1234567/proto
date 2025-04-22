from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMainWindow, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMenuBar, QMenu, QFileDialog
from PyQt6.QtGui import QAction
from canvas import Canvas
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proto")
        self.setGeometry(100, 100, 1200, 800)

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

        # === Editor Tabs (Canvas + Block editors) ===
        self.tabs = QTabWidget()
        self.tabs.setTabBarAutoHide(False)  # <- force tabs to always be visible
        main_layout.addWidget(self.tabs)

        # === Canvas tab ===
        canvas_tab = QWidget()
        canvas_layout = QVBoxLayout(canvas_tab)

        self.canvas = Canvas(self.tabs)  # Pass tab widget so blocks can open editor tabs
        canvas_layout.addWidget(self.canvas)

        self.tabs.setStyleSheet("""
            QTabBar::tab {
                color: black;
            }
        """)

        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)


        self.tabs.addTab(canvas_tab, "Canvas")
        self.tabs.currentChanged.connect(self.on_tab_changed)
        # === Bottom Buttons ===
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        # 1. Create the menu first
        self.add_block_menu = QMenu(self)
        self.add_block_menu.addAction("➕ Add Blank Block", self.canvas.add_block)
        self.add_block_menu.addAction("📦 Import From Library", self.import_from_library)

        # 2. Create the button
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

        # 3. Hook up left-click as usual
        self.add_block_button.clicked.connect(self.canvas.add_block)

        # 4. Now safely install event filter
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
        main_layout.addLayout(bottom_row)

      
        # === Optional: Load stylesheet ===
        try:
            with open("./frontend/styles.qss", "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print("Could not load stylesheet:", e)
        

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

        canvas = self.canvas
        blocks = canvas.blocks
        connections = canvas.connections

        # Build adjacency + dependency graph
        incoming_map = {block: [] for block in blocks}
        outgoing_map = {block: [] for block in blocks}

        for conn in connections:
            incoming_map[conn.end_block].append(conn.start_block)
            outgoing_map[conn.start_block].append(conn.end_block)

        # Topological sort
        sorted_blocks = []
        visited = set()

        sorted_blocks = []
        visited = set()

        def visit(block):
            if block in visited:
                return
            visited.add(block)
            for child in outgoing_map.get(block, []):
                visit(child)
            sorted_blocks.insert(0, block)  # insert at front to maintain topological order


        start_blocks = [b for b in blocks if getattr(b, "is_start_block", False)]
        if not start_blocks:
            print("⚠️ No start block selected. Aborting run.")
            return

        for start in start_blocks:
            visit(start)

        # Now execute blocks in order
        context = {}
        for block in sorted_blocks:
            code = getattr(block, "code", "")
            if not code:
                continue

            try:
                exec(code, context)
                if "run" in context and callable(context["run"]):
                    result = context["run"]()
                    print(f"🧠 Block [{block.name}] ran: result =", result)
                    block._last_output = result  # store for passing if needed
            except Exception as e:
                print(f"❌ Error in block [{block.name}]:", e)
    def save_layout_prompt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Layout", "", "JSON Files (*.json)")
        if path:
            self.canvas.save_layout(path)

    def load_layout_prompt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Layout", "", "JSON Files (*.json)")
        if path:
            self.canvas.load_layout(path)
    
    def import_from_library(self):
        print("📦 Open block library...")  # Placeholder
        # Later: open a dialog to choose a block template
        # selected = open_library_dialog()
        # if selected:
        #     self.canvas.add_block_from_template(selected)

    def eventFilter(self, source, event):
        if source == self.add_block_button and event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton:
                self.add_block_menu.exec(self.add_block_button.mapToGlobal(event.position().toPoint()))
                return True  # Don't pass event on
        return super().eventFilter(source, event)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
