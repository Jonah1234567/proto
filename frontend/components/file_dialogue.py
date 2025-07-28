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


def prompt_load_project_folder(parent=None):
    selected_folder = QFileDialog.getExistingDirectory(
        parent,
        "Open Project Folder",
        str(Path.home()),  # default starting path
        QFileDialog.Option.ShowDirsOnly  # optional — may vary per platform
    )

    if not selected_folder:
        print("❌ No folder selected.")
        return None

    print(f"📁 Selected folder: {selected_folder}")
    return selected_folder
