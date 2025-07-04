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
            })

        
        for conn in self.connections:
            data["connections"].append({
                "start_block": conn.start_block.id,
                "end_block": conn.end_block.id
            })

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Layout saved to {filename}")


def save_to_template(self, path):
    template = {
        "name": self.name,
        "code": self.code,
        "block_type": self.block_type,
        "background_color": self.background_color,
        "inputs": self.inputs.to_dict(),
        "outputs": self.outputs.to_dict(),
        "input_mappings": self.input_mappings
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)

