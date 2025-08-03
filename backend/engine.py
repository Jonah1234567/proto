import subprocess
import tempfile
import json
import sys
from PyQt6.QtCore import QThread, pyqtSignal

def run_all_blocks(window, canvas):
    import subprocess, tempfile, json, sys
    from PyQt6.QtCore import QThread, pyqtSignal

    class StreamReaderThread(QThread):
        line_received = pyqtSignal(str)
        error_received = pyqtSignal(str)
        finished = pyqtSignal()

        def __init__(self, process):
            super().__init__()
            self.process = process

        def run(self):
            while True:
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        self.line_received.emit(line)
                if self.process.stderr:
                    err = self.process.stderr.readline()
                    if err:
                        self.error_received.emit("❌ " + err)
                if self.process.poll() is not None:
                    break
            self.finished.emit()

    # === Extract block data ===
    block_data = []
    for block in canvas.blocks:
        block_data.append({
            "id": block.id,
            "name": block.name,
            "code": block.code,
            "input_mappings": getattr(block, "input_mappings", {}),
            "outputs": getattr(block.outputs, "__dict__", {}),
            "is_start_block": getattr(block, "is_start_block", False),
        })

    # === Write to temp file ===
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w") as temp:
        json.dump({"blocks": block_data}, temp)
        temp_path = temp.name

    # === Run subprocess with unbuffered mode ===
    process = subprocess.Popen(
        [sys.executable, "-u", "backend/block_executor.py", temp_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    # === Store thread as attribute so it's not garbage collected ===
    window.block_runner_thread = StreamReaderThread(process)
    t = window.block_runner_thread
    t.line_received.connect(window.append_output)
    t.error_received.connect(window.append_output)
    t.finished.connect(lambda: window.append_output("✅ All blocks completed.\n"))
    t.start()
