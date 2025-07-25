from PyQt6.QtWidgets import QFileDialog
from pathlib import Path

def prompt_new_project_folder(parent=None):
    selected_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Select or Create New Project Folder",
        str(Path.home() / "NewProject"),
        "Folder Placeholder"
    )

    if not selected_path:
        print("❌ No folder selected.")
        return None

    folder = Path(selected_path)
    if not folder.exists():
        folder.mkdir(parents=True)
        print(f"✅ Created folder: {folder}")

    return str(folder)
