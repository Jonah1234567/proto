from pathlib import Path
import json


class Project:
    def __init__(self, base_path: str, project_type: str = "default"):
        self.name = Path(base_path).name
        self.base_path = Path(base_path)
        self.project_type = project_type

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
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data.get("name", ""),
            base_path=data.get("base_path", ""),
            project_type=data.get("project_type", "default"), 
        )

    def save(self):
        with open(self.project_file, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def load(cls, path: str):
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
