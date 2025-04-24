from inputs_proxy import InputsProxy
from outputs_proxy import OutputsProxy
def run_block(code: str, input_dict: dict):
    local_scope = {}
    inputs = InputsProxy(input_dict)
    outputs = OutputsProxy()

    local_scope["inputs"] = inputs
    local_scope["outputs"] = outputs

    exec(code, {}, local_scope)

    return outputs.to_dict()
