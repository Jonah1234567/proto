# app_controller.py
from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from welcome_screen import WelcomeScreen
from hadron_designer import HadronDesignerWindow
from new_project_configuration_screen import NewProjectConfigurationScreen
from under_construction_screen import UnderConstructionScreen 
from components.file_dialogue import prompt_new_project_folder

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.project import Project

class AppController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proto")
        self.setGeometry(100, 100, 1200, 800)

        self.project = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Initialize screens
        self.welcome_screen = WelcomeScreen(self)
        self.editor_view = HadronDesignerWindow(self)
        self.new_project_configuration_screen = NewProjectConfigurationScreen(self)
        self.under_construction_screen = UnderConstructionScreen(self)

        self.stack.addWidget(self.welcome_screen)
        self.stack.addWidget(self.editor_view)
        self.stack.addWidget(self.new_project_configuration_screen)
        self.stack.addWidget(self.under_construction_screen)
        

        self.stack.setCurrentWidget(self.welcome_screen)
        self.history = [self.welcome_screen]

    def switch_to_new_project(self, project_type):
        project_path = prompt_new_project_folder()
        if project_path == None:
            return
        
        self.project = Project(project_path, project_type)


        current = self.stack.currentWidget()
        if current is not self.editor_view:
            self.history.append(current)
        self.stack.setCurrentWidget(self.editor_view)  

    def switch_to_new_project_configuration(self):
        current = self.stack.currentWidget()
        if current is not self.new_project_configuration_screen:
            self.history.append(current)
        self.stack.setCurrentWidget(self.new_project_configuration_screen)

    def switch_to_under_construction(self):
        current = self.stack.currentWidget()
        if current is not self.under_construction_screen:
            self.history.append(current)
        self.stack.setCurrentWidget(self.under_construction_screen)

    def switch_back(self):
        if self.history:
            previous_widget = self.history.pop()
            self.stack.setCurrentWidget(previous_widget)

    

    


