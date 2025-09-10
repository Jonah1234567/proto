from PyQt6.QtWidgets import (
    QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
import re

try:
    # Optional: canonicalizes names the same way pip does (nice to have)
    from packaging.utils import canonicalize_name as _canon_name
except Exception:
    _canon_name = None


class RequirementsEditor(QWidget):
    """
    A reusable widget for managing pip-style requirements (e.g., ['numpy', 'pandas==2.2.2']).

    - Loads existing entries from an object attribute (default: 'requirements')
    - Prevents duplicate packages, asks to replace if version differs
    - Exposes get_requirements()/set_requirements() and a 'modified' signal
    """

    modified = pyqtSignal()

    def __init__(self, parent=None, *, initial=None, block=None, attr_name: str = "requirements", title="Requirements (pip packages)"):
        super().__init__(parent)
        self._attr_name = attr_name
        # Decide initial list
        if initial is not None:
            entries = list(initial)
        elif block is not None:
            entries = list(getattr(block, attr_name, None) or [])
        else:
            entries = []

        # --- UI ---
        root = QVBoxLayout(self)
        box = QGroupBox(title)
        root.addWidget(box)

        v = QVBoxLayout(box)

        self.list = QListWidget()
        self.list.setStyleSheet("""
        QListWidget {
            background: white;
            color: black;
            border: 1px solid #ccc;
            border-radius: 6px;
        }

        /* Vertical scrollbar */
        QScrollBar:vertical {
            border: none;
            background: #f0f0f0;
            width: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical {
            background: #b0bec5;
            min-height: 20px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical:hover {
            background: #90a4ae;
        }

        QScrollBar::handle:vertical:pressed {
            background: #78909c;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }

        /* Horizontal scrollbar (in case of long package names) */
        QScrollBar:horizontal {
            border: none;
            background: #f0f0f0;
            height: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }

        QScrollBar::handle:horizontal {
            background: #b0bec5;
            min-width: 20px;
            border-radius: 5px;
        }

        QScrollBar::handle:horizontal:hover {
            background: #90a4ae;
        }

        QScrollBar::handle:horizontal:pressed {
            background: #78909c;
        }

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }

        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        """)

        self.list.setFixedHeight(60)  # make this dynamic later

        v.addWidget(self.list)

        # Inputs + buttons
        row = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("package (e.g., numpy)")
        self.ver_input = QLineEdit()
        self.ver_input.setPlaceholderText("version (optional)")
        self.add_btn = QPushButton("➕ Add")
        self.rm_btn = QPushButton("🗑️ Remove Selected")
        row.addWidget(self.name_input)
        row.addWidget(self.ver_input)
        row.addWidget(self.add_btn)
        v.addLayout(row)
        v.addWidget(self.rm_btn)

        # Styling
        for w in (self.name_input, self.ver_input):
            w.setStyleSheet("QLineEdit { background:white; color:black; border:1px solid #ccc; border-radius:6px; padding:4px; }")
      
        # Wire
        self.add_btn.clicked.connect(self.add_requirement)
        self.rm_btn.clicked.connect(self.remove_selected)

        # Load initial
        self._load_entries(entries)

    # ---------- Public API ----------

    def get_requirements(self) -> list[str]:
        """Return a clean list of strings like ['numpy', 'pandas==2.2.2']."""
        dep_map = {}  # canon_name -> (raw_name, version)
        for i in range(self.list.count()):
            text = self.list.item(i).text().strip()
            c, raw, ver = self._parse(text)
            if raw:
                dep_map[c] = (raw, ver)
        result = []
        for _, (raw, ver) in dep_map.items():
            result.append(self._display(raw, ver))
        return result

    def set_requirements(self, entries: list[str | dict]):
        """Replace the current list with 'entries' (strings or {'name','version'} dicts)."""
        self.list.clear()
        self._load_entries(entries)
        self.modified.emit()

    def has_requirement(self, package_name: str) -> bool:
        return self._find_index(self._canon(package_name)) != -1

    # ---------- Slots / Handlers ----------

    def add_requirement(self):
        self.modified.emit()
        raw_name = self.name_input.text().strip()
        ver = self.ver_input.text().strip()

        if not raw_name:
            QMessageBox.warning(self, "Missing package", "Please enter a package name (e.g., numpy).")
            return

        canon = self._canon(raw_name)
        new_text = self._display(raw_name, ver)

        idx = self._find_index(canon)
        if idx != -1:
            _, raw_existing, ver_existing = self._parse(self.list.item(idx).text())
            if (ver or "") == (ver_existing or ""):
                QMessageBox.information(self, "Already listed", f"'{new_text}' is already present.")
                return

            resp = QMessageBox.question(
                self,
                "Replace version?",
                f"Package '{raw_name}' is already '{raw_existing}{'=='+ver_existing if ver_existing else ''}'.\n"
                f"Replace with '{new_text}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resp != QMessageBox.StandardButton.Yes:
                return
            self.list.item(idx).setText(new_text)
        else:
            self.list.addItem(new_text)

        self.name_input.clear()
        self.ver_input.clear()

    def remove_selected(self):
        self.modified.emit()
        rows = sorted({idx.row() for idx in self.list.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "Nothing selected", "Select a requirement to remove.")
            return
        for r in rows:
            self.list.takeItem(r)

    # ---------- Helpers ----------

    def _load_entries(self, entries):
        seen = set()
        for dep in entries:
            if isinstance(dep, dict):
                raw_name = str(dep.get("name", "")).strip()
                raw_ver = str(dep.get("version", "")).strip()
            else:
                raw = str(dep).strip()
                if "==" in raw:
                    raw_name, raw_ver = raw.split("==", 1)
                    raw_name, raw_ver = raw_name.strip(), raw_ver.strip()
                else:
                    raw_name, raw_ver = raw, ""
            if not raw_name:
                continue
            key = self._canon(raw_name)
            if key in seen:
                continue
            seen.add(key)
            self.list.addItem(self._display(raw_name, raw_ver))

    def _canon(self, s: str) -> str:
        s = (s or "").strip()
        if _canon_name:
            try:
                return _canon_name(s)
            except Exception:
                pass
        return re.sub(r"[-_.]+", "-", s.lower())

    def _display(self, name: str, ver: str = "") -> str:
        name = (name or "").strip()
        ver = (ver or "").strip()
        return f"{name}=={ver}" if ver else name

    def _parse(self, text: str):
        text = (text or "").strip()
        if "==" in text:
            raw_name, ver = text.split("==", 1)
            return self._canon(raw_name), raw_name.strip(), ver.strip()
        return self._canon(text), text, ""

    def _find_index(self, canon_name: str) -> int:
        for i in range(self.list.count()):
            c, _, _ = self._parse(self.list.item(i).text())
            if c == canon_name:
                return i
        return -1
