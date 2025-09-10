import json
from PyQt6.QtWidgets import QFileDialog
import json

def save_file(self, filename):
        data = {
            "blocks": [],
            "connections": []
        }

        for block in self.blocks:
            
            print(block.input_mappings if hasattr(block.input_mappings, "to_dict") else {}, "hi")
            data["blocks"].append({
                "id": block.id,
                "name": block.name,
                "block_type" : block.block_type,
                "background_color" : block.background_color,
                "x": block.pos().x(),
                "y": block.pos().y(),
                "code": getattr(block, "code", ""),
                "inputs": block.inputs.to_dict() if hasattr(block.inputs, "to_dict") else {},
                "outputs": block.outputs.to_dict() if hasattr(block.outputs, "to_dict") else {},
                "input_mappings": block.input_mappings if hasattr(block, "input_mappings") else {},
                "is_start_block": getattr(block, "is_start_block", False),
                "dependencies": block.dependencies,
            })

        
        for conn in self.connections:
            data["connections"].append({
                "start_block": conn.start_block.id,
                "end_block": conn.end_block.id
            })

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Layout saved to {filename}")



def save_to_template(block):
    pth = None
    if block.filepath != None:
         pth = block.filepath

    path, _ = QFileDialog.getSaveFileName(
        None,
        "Save Block as Template",
        pth,
        "Block Templates (*.hdrn)"
    )

    if not path:
        return  # User cancelled

    if not path.endswith(".hdrn"):
        path += ".hdrn"

    template = {
        "name": block.name,
        "code": block.code,
        "block_type": block.block_type,
        "background_color": block.background_color,
        "inputs": block.inputs.to_dict(),
        "outputs": block.outputs.to_dict(),
        "input_mappings": block.input_mappings,
        "dependencies": block.dependencies
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)

    block.filepath = path

    print(f"✅ Block saved to template: {path}")

