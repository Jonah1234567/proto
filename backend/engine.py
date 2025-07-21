import sys
from pathlib import Path
from types import SimpleNamespace
import io
import contextlib

sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.inputs_proxy import InputsProxy
from backend.outputs_proxy import OutputsProxy
original_stdout = sys.stdout.write
original_stderr = sys.stderr.write


def run_block(window, canvas, block, context, code):
    all_blocks_by_id = {block.id: block for block in canvas.blocks}

    

    # === Step 1: Gather input values
    inputs = {}
    for input_name, mapping in getattr(block, "input_mappings", {}).items():
        source_block_id = mapping.get("block_id")
        source_output_name = mapping.get("output_name")

        source_block = all_blocks_by_id.get(source_block_id)
        if source_block and hasattr(source_block, "outputs"):
            value = getattr(source_block.outputs, source_output_name, None)
            inputs[input_name] = value
        else:
            inputs[input_name] = None  # Fallback if missing

    print(inputs)
    # === Step 2: Prepare local execution context
    local_vars = {
        "inputs": SimpleNamespace(**inputs),
        "outputs": SimpleNamespace()
    }


    # === Step 3: Execute the block's code
    try:
        sys.stdout.write = window.redirector
        sys.stderr.write = window.redirector

        exec(code)

        sys.stdout.write = original_stdout
        sys.stderr.write = original_stderr


    except Exception as e:
        print(f"❌ Error in block [{block.name}]:", e)

    if hasattr(local_vars["outputs"], "__dict__"):
        print(local_vars["outputs"].__dict__.items())
        for key, value in local_vars["outputs"].__dict__.items():
            setattr(block.outputs, key, value)
   

def run_all_blocks(window, canvas):
    blocks = canvas.blocks
    connections = canvas.connections

    # Build adjacency + dependency graph
    incoming_map = {block: [] for block in blocks}
    outgoing_map = {block: [] for block in blocks}

    for conn in connections:
        incoming_map[conn.end_block].append(conn.start_block)
        outgoing_map[conn.start_block].append(conn.end_block)

    # Topological sort
    sorted_blocks = []
    visited = set()

    sorted_blocks = []
    visited = set()

    def visit(block):
        if block in visited:
            return
        visited.add(block)
        for child in outgoing_map.get(block, []):
            visit(child)
        sorted_blocks.insert(0, block)  # insert at front to maintain topological order


    start_blocks = [b for b in blocks if getattr(b, "is_start_block", False)]
    if not start_blocks:
        print("⚠️ No start block selected. Aborting run.")
        return

    for start in start_blocks:
        visit(start)

    # Now execute blocks in order
    context = {}
    for block in sorted_blocks:
        print(block.name)
        code = getattr(block, "code", "")
        if not code:
            continue

        run_block(window, canvas, block, context, code)

        
