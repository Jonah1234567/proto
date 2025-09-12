import sys
import re
import importlib.metadata as im
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QTreeWidget, QTreeWidgetItem,
    QListWidget, QPushButton, QLabel, QLineEdit, QMessageBox
)
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtGui import QColor, QBrush
import threading
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QProgressDialog, QMessageBox

sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.utils.requirements_manager import collect_installed_requirements, reinstall_packages, install_packages
# Optional: use packaging to parse requirements & compare versions
try:
    from packaging.requirements import Requirement as _PkgRequirement
    from packaging.utils import canonicalize_name as _canon_name
except Exception:
    _PkgRequirement = None
    def _canon_name(s: str) -> str:
        return re.sub(r"[-_.]+", "-", s).lower()
import json

class RequirementsOverviewDialog(QDialog):
    installFinished = pyqtSignal(bool, list)  # (ok, errors)
    """
    Popup dialog that shows:
      - Required libraries collected from all blocks (Package, Spec, Installed, Status)
      - All installed libraries in the current environment (side by side)
    """
    def __init__(self, parent, controller, required_specs: dict[str, set[str]]):
        super().__init__(parent)
        self._python_path = controller.project.python_path
        self._required_specs_raw = required_specs  # keep original specs by canon name

        self._progress = None
        self.installFinished.connect(self._on_install_finished)

        self.setWindowTitle("Environment Requirements")
        self.setModal(True)
        self.resize(1100, 600)
        self.controller = controller

        # Light theme: white background, black text
        self.setStyleSheet("""
            QDialog {
                background: white;
                color: black;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 10px;
                color: black;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 8px;
            }
            QTreeWidget, QListWidget {
                border: 1px solid #ddd;
                outline: none;
                background: white;
                color: black;
            }
            QHeaderView::section {
                background: #f0f0f0;
                color: black;
                padding: 4px 6px;
                border: 1px solid #ccc;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                background: white;
                color: black;
            }
            QPushButton {
                background-color: #f5f5f5;
                color: black;
                border: 1px solid #bbb;
                border-radius: 4px;
                padding: 5px 12px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #eaeaea; }
            QPushButton:pressed { background-color: #dcdcdc; }
        """)

        # --- Layout: side by side ---
        outer = QVBoxLayout(self)
        lists_row = QHBoxLayout()
        outer.addLayout(lists_row, 1)

        # ----- Left: required -----
        gb_required = QGroupBox("Required by Blocks")
        v_req = QVBoxLayout(gb_required)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Package", "Requested Versions", "Installed Version", "Status"])
        self.tree.setUniformRowHeights(True)
        self.tree.setRootIsDecorated(False)

        hdr = self.tree.header()
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)       # Package
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)       # Requested Versions
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Installed Version
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Status

        v_req.addWidget(self.tree)
        lists_row.addWidget(gb_required, 2)

        # ----- Right: installed -----
        gb_inst = QGroupBox("Installed in Environment")
        v_inst = QVBoxLayout(gb_inst)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit(placeholderText="Type to filter installed packages…")
        self.filter_edit.textChanged.connect(self._filter_installed)
        search_row.addWidget(self.filter_edit)
        v_inst.addLayout(search_row)

        self.inst_list = QListWidget()
        self.inst_list.setSpacing(1)
        v_inst.addWidget(self.inst_list, 1)

        # Optional: show interpreter used
        env_note = QLabel(f"Using: {sys.executable}")
        env_note.setStyleSheet("color: #555; font-size: 11px;")
        v_inst.addWidget(env_note)

        lists_row.addWidget(gb_inst, 1)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        self.autofix_btn = QPushButton("Auto-fix Version Mismatches")
        self.autofix_btn.clicked.connect(self._autofix_mismatches)
        btn_row.addWidget(self.autofix_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        outer.addLayout(btn_row)

        # Data
        self._installed = collect_installed_requirements(self._python_path, _canon_name)
        self._populate_required(required_specs, self._installed)
        self._populate_installed(self._installed)

    # ---- Data helpers ----
    

    def _populate_installed(self, installed: dict):
        self.inst_list.clear()
        items = [f"{meta['name']}=={meta['version']}" for meta in installed.values()]
        items.sort(key=lambda s: s.lower())
        self.inst_list.addItems(items)

    def _populate_required(self, required_specs: dict[str, set[str]], installed: dict):
        self.tree.clear()
        for canon_name in sorted(required_specs.keys()):

            specs = sorted(required_specs[canon_name])
            if specs:
                spec_parts = [
                    self._extract_versions_only(s, canon_name) for s in specs
                ]
                # Drop empties and join
                spec_text = ", ".join([p for p in spec_parts if p])
            else:
                spec_text = ""



            if canon_name in installed:
                inst_ver = installed[canon_name]["version"]
                status = self._status_for_specs(specs, inst_ver)
                inst_disp = inst_ver
            else:
                status = "Missing"
                inst_disp = "—"

            display_name = next(iter(specs)).split()[0] if specs else canon_name
            if canon_name in installed:
                display_name = installed[canon_name]["name"]

            item = QTreeWidgetItem([display_name, spec_text, inst_disp, status])

            if status == "OK":
                item.setForeground(3, Qt.GlobalColor.darkGreen)
            elif status == "Version mismatch":
                item.setForeground(3, Qt.GlobalColor.darkYellow)
            elif status == "Conflict":
                # Stronger red + hint to reconcile
                item.setText(3, "Conflict (needs reconcile)")
                item.setForeground(3, QBrush(QColor(200, 0, 0)))
            else:  # Missing
                item.setForeground(3, Qt.GlobalColor.red)

            self.tree.addTopLevelItem(item)


    def _status_for_specs(self, specs: list[str], installed_version: str) -> str:
        if not specs:
            return "OK"
        if _PkgRequirement is None:
            for s in specs:
                m = re.search(r"==\s*([^\s,]+)", s)
                if m and m.group(1) != installed_version:
                    return "Version mismatch"
            return "OK"
        for s in specs:
            try:
                r = _PkgRequirement(s) if any(op in s for op in "<>!=~") else _PkgRequirement(f"{s} ")
                if r.specifier and not r.specifier.contains(installed_version, prereleases=True):
                    return "Version mismatch"
            except Exception:
                continue
        return "OK"

    def _filter_installed(self, text: str):
        t = (text or "").strip().lower()
        for i in range(self.inst_list.count()):
            item = self.inst_list.item(i)
            item.setHidden(t not in item.text().lower())

    def _has_pin_conflict(self, specs: list[str]) -> tuple[bool, set[str]]:
        """
        Returns (conflict, pinned_versions).
        Conflict = True if multiple distinct '==' pins are present (e.g., 1.26.4 vs 2.0.0).
        """
        pinned = set()
        for s in specs:
            m = re.search(r"==\s*([^\s,]+)", s)
            if m:
                pinned.add(m.group(1).strip())
        return (len(pinned) > 1, pinned)

    def _status_for_specs(self, specs: list[str], installed_version: str) -> str:
        # Detect conflicting hard pins first: numpy==1.x vs numpy==2.x
        conflict, pins = self._has_pin_conflict(specs)
        if conflict:
            return "Conflict"

        # No explicit spec means just "installed"
        if not specs:
            return "OK"

        if _PkgRequirement is None:
            # Fallback: only check '==' pins if packaging isn't available
            for s in specs:
                m = re.search(r"==\s*([^\s,]+)", s)
                if m and m.group(1) != installed_version:
                    return "Version mismatch"
            return "OK"

        # Use proper spec parsing with packaging (best-effort)
        for s in specs:
            try:
                r = _PkgRequirement(s) if any(op in s for op in "<>!=~") else _PkgRequirement(f"{s} ")
                if r.specifier and not r.specifier.contains(installed_version, prereleases=True):
                    return "Version mismatch"
            except Exception:
                # If parsing fails, be forgiving
                continue
        return "OK"

    def _extract_versions_only(self, spec: str, pkg_name: str) -> str:
        """
        Extract only the version numbers from a requirement string.
        Examples:
            'numpy==1.26.4'       -> '1.26.4'
            'numpy>=1.20,<2.0'    -> '1.20, 2.0'
            'numpy'               -> ''
        """
        s = spec.strip()
        # Remove package name if it starts with it
        if s.lower().startswith(pkg_name.lower()):
            s = s[len(pkg_name):].strip()

        # Find all version-like tokens (numbers + dots + letters)
        matches = re.findall(r"(\d+(?:\.\d+)*[a-zA-Z0-9]*)", s)
        return ", ".join(matches)

    def _summarize_packages(self):
        """
        Recompute statuses from current required+installed sets.
        Returns dict:
          { canon_name: {
              'display': str,
              'installed': 'x.y.z' or None,
              'status': 'OK'|'Missing'|'Version mismatch'|'Conflict',
              'specs': set[str]
            } }
        """
        out = {}
        for canon, specs in self._required_specs_raw.items():
            specs_list = sorted(specs)
            installed_ver = self._installed.get(canon, {}).get("version")
            display = self._installed.get(canon, {}).get("name", canon)

            status = "OK"
            # conflict first
            conflict, _pins = self._has_pin_conflict(specs_list)
            if conflict:
                status = "Conflict"
            else:
                # evaluate against installed
                if installed_ver is None:
                    status = "Missing"
                else:
                    st = self._status_for_specs(specs_list, installed_ver)
                    status = st

            out[canon] = {
                "display": display,
                "installed": installed_ver,
                "status": status,
                "specs": set(specs_list),
            }
        return out

    def _pick_desired_spec(self, specs: set[str], canon_name: str) -> str:
        """
        Choose a single requirement string to install for a mismatch (no conflicts).
        Preference:
          1) A hard pin '==' (if multiple identical, that's fine; conflicts were filtered).
          2) Otherwise, any non-empty specifier string (e.g., '>=1.21,<2').
          3) Otherwise, just the bare package (empty string after name stripped).
        Returns the *specifier* part appended to package name when installing
        (e.g., '==1.26.4' or '>=1.21,<2'); may be '' for bare package.
        """
        # Collect pins and general specs
        pins = []
        general = []
        for s in specs:
            t = s.strip()
            # Drop leading package name if present
            if t.lower().startswith(canon_name.lower()):
                t = t[len(canon_name):].strip()
            if "==" in t:
                pins.append(t)
            elif any(op in t for op in (">", "<", "!", "~", "=")):
                general.append(t)
        if pins:
            # If multiple identical pins, they won't be a conflict; just use the first
            return pins[0]
        if general:
            return general[0]
        return ""  # bare

    def _has_any(self, summary: dict, status: str) -> bool:
        return any(info["status"] == status for info in summary.values())

    def _autofix_mismatches(self):
        summary = self._summarize_packages()

        # 1) Block on conflicts
        if self._has_any(summary, "Conflict"):
            conflicters = [info["display"] or canon for canon, info in summary.items() if info["status"] == "Conflict"]
            QMessageBox.warning(
                self,
                "Conflicting Requirements",
                "Some packages have conflicting version pins between blocks:\n\n"
                + "\n".join(f"• {pkg}" for pkg in conflicters)
                + "\n\nPlease reconcile the requested versions before auto-fixing."
            )
            return

        # 2) Build work: only uninstall on mismatches; install for mismatches & missing
        to_uninstall_then_install = []  # (pkg_name, spec_suffix) – ONLY for Version mismatch
        to_install_missing = []         # (pkg_name, spec_suffix)

        for canon, info in summary.items():
            status = info["status"]
            if status not in ("Version mismatch", "Missing"):
                continue

            pkg_name = info["display"] if info["display"] else canon
            spec_suffix = self._pick_desired_spec(info["specs"], canon)  # '==1.2.3', '>=1,<2', or ''

            if status == "Version mismatch":
                # Only uninstall if we actually have a target spec (avoid uninstall→bare reinstall surprises)
                to_uninstall_then_install.append((pkg_name, spec_suffix))
            else:  # Missing
                to_install_missing.append((pkg_name, spec_suffix))

        if not to_uninstall_then_install and not to_install_missing:
            QMessageBox.information(self, "Up to Date", "All packages installed already.")
            return

        # 3) Execute with the same interpreter/env
        self.autofix_btn.setEnabled(False)
        self.autofix_btn.setText("Installing…")

        def worker():
            ok = True
            errors = []

            # A) Version mismatches: uninstall (only here), then install
            ok, errors = reinstall_packages(self._python_path, to_uninstall_then_install, ok, errors)

            # B) Missing: install directly (no uninstall)
            ok, errors = install_packages(self._python_path, to_install_missing, ok, errors)
            
            self.installFinished.emit(ok, errors)



        # Show busy dialog right away on the GUI thread
        self._progress = QProgressDialog("Installing packages…", None, 0, 0, self)
        self._progress.setWindowTitle("Please wait")
        self._progress.setCancelButton(None)      # no cancel button
        self._progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._progress.setAutoClose(False)
        self._progress.setAutoReset(False)
        self._progress.show()

        # Launch the worker
        threading.Thread(target=worker, daemon=True).start()


    def _on_install_finished(self, ok: bool, errors: list[str]):
        # Close busy popup safely
        if self._progress is not None:
            self._progress.close()
            self._progress = None

        # Re-enable button etc.
        self.autofix_btn.setEnabled(True)
        self.autofix_btn.setText("Auto-fix Version Mismatches")

        # Refresh UI state
        self._installed = collect_installed_requirements(self._python_path, _canon_name)
        self._populate_installed(self._installed)
        self._populate_required(self._required_specs_raw, self._installed)

        # Now show the final result popup
        if ok and not errors:
            QMessageBox.information(self, "Success",
                                    "Missing packages installed and version mismatches resolved.")
        elif ok:
            QMessageBox.information(self, "Completed with Notes",
                                    "Operations completed with some messages:\n\n" + "\n\n".join(errors[:8]))
        else:
            QMessageBox.critical(self, "Some Installs Failed",
                                "One or more operations failed:\n\n" + "\n\n".join(errors[:12]))
