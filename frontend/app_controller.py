# app_controller.py
from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from welcome_screen import WelcomeScreen
from hadron_designer import HadronDesignerWindow
from new_project_configuration_screen import NewProjectConfigurationScreen

class AppController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proto")
        self.setGeometry(100, 100, 1200, 800)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Initialize screens
        self.welcome_screen = WelcomeScreen(self)
        self.editor_view = HadronDesignerWindow(self)
        self.new_project_configuration_screen = NewProjectConfigurationScreen(self)

        self.stack.addWidget(self.welcome_screen)
        self.stack.addWidget(self.editor_view)
        self.stack.addWidget(self.new_project_configuration_screen)
        

        self.stack.setCurrentWidget(self.welcome_screen)

    def switch_to_editor(self):
        self.stack.setCurrentWidget(self.editor_view)

    def switch_to_new_project_configuration(self):
        self.stack.setCurrentWidget(self.new_project_configuration_screen)
