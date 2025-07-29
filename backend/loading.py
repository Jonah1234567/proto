import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from backend.inputs_proxy import InputsProxy
from backend.outputs_proxy import OutputsProxy


from frontend.block import Block
from frontend.connection import Connection

def load_file(self, filename):
    print("fire")
    with open(filename, "r") as f:
        data = json.load(f)

    # Clear current layout
    for block in self.blocks:
        self.scene.removeItem(block)
    for conn in self.connections:
        conn.remove()
    self.blocks.clear()
    self.connections.clear()

    # Recreate blocks
    id_to_block = {}
    for block_data in data["blocks"]:
        block = Block(block_data["name"], self.tab_widget)
        block.block_type = block_data["block_type"]
        block.id = block_data["id"]
        block.background_color = block_data["background_color"]
        block.code = block_data.get("code", "")
        block.inputs = InputsProxy()
        block.inputs.from_dict(block_data.get("inputs", {}))
        block.outputs = OutputsProxy()
        block.outputs.from_dict(block_data.get("outputs", {}))
        block.input_mappings = block_data.get("input_mappings", {})
        block.is_start_block = block_data.get("is_start_block", False)
        block.setPos(block_data["x"], block_data["y"])
        self.scene.addItem(block)
        self.blocks.append(block)
        id_to_block[block.id] = block

    # Recreate connections
    for conn_data in data["connections"]:
        start = id_to_block.get(conn_data["start_block"])
        end = id_to_block.get(conn_data["end_block"])
        if start and end:
            conn = Connection(start, end, self.scene)
            self.connections.append(conn)

def load_block_from_template(self, template):
    name = template.get("name", "Unnamed Block")
    code = template.get("code", "")
    block_type = template.get("block_type", "code")
    background_color =  template.get("background_color", "#74b9ff")
    inputs = InputsProxy()
    inputs.from_dict(template.get("inputs", {}))

    outputs = OutputsProxy()
    outputs.from_dict(template.get("outputs", {}))
    input_mappings = template.get("input_mappings", {})

    block = Block(name, self.tab_widget, background_color)
    block.block_type = block_type
    block.code = code
    block.inputs = inputs
    block.outputs = outputs
    block.input_mappings = input_mappings
    block.setPos(100 + len(self.blocks) * 30, 100 + len(self.blocks) * 20)

    return block
    