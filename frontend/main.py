from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMainWindow, QTabWidget
)
from PyQt6.QtCore import Qt
from canvas import Canvas
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proto")
        self.setGeometry(100, 100, 1200, 800)

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

        self.add_block_button.clicked.connect(self.canvas.add_block)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
