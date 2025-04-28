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