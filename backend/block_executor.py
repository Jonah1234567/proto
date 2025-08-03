# block_executor.py

import sys
import json
from pathlib import Path
from types import SimpleNamespace
import io
import functools
print = functools.partial(print, flush=True)

# Force UTF-8 encoding for stdout/stderr to allow emoji characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def topological_sort(blocks):
    from collections import defaultdict, deque

    id_to_block = {b["id"]: b for b in blocks}
    indegree = defaultdict(int)
    graph = defaultdict(list)

    for b in blocks:
        for mapping in b.get("input_mappings", {}).values():
            if mapping and mapping.get("block_id") in id_to_block:
                graph[mapping["block_id"]].append(b["id"])
                indegree[b["id"]] += 1

    queue = deque([b["id"] for b in blocks if indegree[b["id"]] == 0])
    sorted_blocks = []

    while queue:
        bid = queue.popleft()
        sorted_blocks.append(id_to_block[bid])
        for neighbor in graph[bid]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_blocks) != len(blocks):
        print("⚠️ Cycle detected or incomplete graph!")
    return sorted_blocks

def run_all_from_data(path):
    import sys
    from types import SimpleNamespace

    with open(path, "r") as f:
        data = json.load(f)

    blocks = topological_sort(data["blocks"])

    block_map = {b["id"]: b for b in blocks}
    variables = {}
    counter = 0

    for block in blocks:
        try:
            counter += 1
            print(f"\n🔹 [{counter}] Running: {block['name']}")

            inputs = {}
            for input_name, mapping in block.get("input_mappings", {}).items():
                source_id = mapping.get("block_id")
                output_name = mapping.get("output_name")

                source_outputs = variables.get(source_id)
                if isinstance(source_outputs, SimpleNamespace):
                    inputs[input_name] = getattr(source_outputs, output_name, None)
                else:
                    inputs[input_name] = None  # or raise an error here if required

            local_vars = {
                "inputs": SimpleNamespace(**inputs),
                "outputs": SimpleNamespace()
            }

            exec(block["code"], {}, local_vars)

            outputs_ns = local_vars["outputs"]
            if not isinstance(outputs_ns, SimpleNamespace):
                raise ValueError("outputs must be a SimpleNamespace")

            variables[block["id"]] = outputs_ns
            if counter == 2:
                print(f"✅ [{block['name']}] finished with outputs: {vars(outputs_ns)}")

        except Exception as e:
            print(f"❌ [{block['name']}] error: {e}", file=sys.stderr)

if __name__ == "__main__":
    run_all_from_data(sys.argv[1])
