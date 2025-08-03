from pathlib import Path
import json
import sys
import subprocess

class Project:
    def __init__(self, base_path: str, project_type: str = "hadron", terminal_status=False, gen_env=False, env_path='', pip_path='', python_path=''):
        self.name = Path(base_path).name
        self.base_path = Path(base_path)
        self.project_type = project_type
        self.open_terminal = terminal_status
        if gen_env:
            self.env_path, self.pip_path, self.python_path = self.create_env()
        else:
            self.env_path, self.pip_path, self.python_path = env_path, pip_path, python_path

        # Optionally create project folder
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.save()

    @property
    def project_file(self):
        return self.base_path / "project_settings.json"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "base_path": str(self.base_path),
            "project_type": self.project_type,
            "open_terminal": self.open_terminal,
            "env_path" : str(self.env_path),
            "pip_path" : str(self.pip_path),
            "python_path" : str(self.python_path) 
        }

    def save(self):
        with open(self.project_file, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    def create_env(self):
        print("Making new env")
        venv_path = self.base_path / "project_env"
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

        if sys.platform == "win32":
            pip_path = venv_path / "Scripts" / "pip.exe"
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
            python_path = venv_path / "bin" / "python"

        return venv_path, pip_path, python_path

def load_project( path: str):
    with open(path, "r") as f:
        data = json.load(f)
        print(data)
    return data
