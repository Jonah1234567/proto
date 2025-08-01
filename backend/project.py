from pathlib import Path
import json


class Project:
    def __init__(self, base_path: str, project_type: str = "hadron", terminal_status=False):
        self.name = Path(base_path).name
        self.base_path = Path(base_path)
        self.project_type = project_type
        self.open_terminal = terminal_status

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
        }

    def save(self):
        with open(self.project_file, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

  
def load_project( path: str):
    with open(path, "r") as f:
        data = json.load(f)
        print(data)
    return data
