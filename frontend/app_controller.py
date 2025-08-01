# app_controller.py
from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from welcome_screen import WelcomeScreen
from hadron_designer import HadronDesignerWindow
from new_project_configuration_screen import NewProjectConfigurationScreen
from under_construction_screen import UnderConstructionScreen 
from components.file_dialogue import prompt_new_project_folder, prompt_load_project_folder

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.project import Project
from backend.project import load_project


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
        self.stack.addWidget(self.welcome_screen)
        

        self.stack.setCurrentWidget(self.welcome_screen)
        self.history = [self.welcome_screen]

    def switch_to_new_project(self, project_type):
        project_path = prompt_new_project_folder()
        if project_path == None:
            return
        
        self.project = Project(project_path, project_type)

        self.editor_view = HadronDesignerWindow(self)
        self.stack.addWidget(self.editor_view)

        current = self.stack.currentWidget()
        if current is not self.editor_view:
            self.history.append(current)
        self.stack.setCurrentWidget(self.editor_view)  

    def switch_to_new_project_configuration(self):
        self.new_project_configuration_screen = NewProjectConfigurationScreen(self)
        self.stack.addWidget(self.new_project_configuration_screen)

        current = self.stack.currentWidget()
        if current is not self.new_project_configuration_screen:
            self.history.append(current)
        self.stack.setCurrentWidget(self.new_project_configuration_screen)

    def switch_to_under_construction(self):
        self.under_construction_screen = UnderConstructionScreen(self)
        self.stack.addWidget(self.under_construction_screen)

        current = self.stack.currentWidget()
        if current is not self.under_construction_screen:
            self.history.append(current)
        self.stack.setCurrentWidget(self.under_construction_screen)

    def switch_back(self):
        if self.history:
            previous_widget = self.history.pop()
            self.stack.setCurrentWidget(previous_widget)

    def switch_to_existing_project(self):
        path = prompt_load_project_folder()

        if path == None:
            return

        project_data = load_project(Path(path) / "project_settings.json")
        self.project = Project(project_data['base_path'], project_data['project_type'], project_data['open_terminal'])
        
        self.editor_view = HadronDesignerWindow(self)
        self.stack.addWidget(self.editor_view)

        current = self.stack.currentWidget()
        if current is not self.editor_view:
            self.history.append(current)
        self.stack.setCurrentWidget(self.editor_view)  


    

    


