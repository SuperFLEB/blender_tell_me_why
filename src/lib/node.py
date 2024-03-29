from dataclasses import dataclass
from bpy.types import Node, NodeSocket

def socket_type_label(socket: NodeSocket):
    return {
        socket.type: socket.type.capitalize(),
        "INT": "Integer",
        "VALUE": "Float",
        "STRING": "String",
        "VECTOR": "X, Y, Z",
        "RGBA": "R, G, B, A",
        "SHADER": "Node",
        "OBJECT": "Object",
        "IMAGE": "Image",
        "TEXTURE": "Texture",
        "MATERIAL": "Material",
        "COLLECTION": "Collection"
    }[socket.type]


def default_value_string(socket: NodeSocket, unprintable: str = "---", float_fix: int = 3):
    def fix(val):
        return f"{{0:.{float_fix}f}}".format(val)

    if not hasattr(socket, "default_value"):
        return unprintable
    # There are probably some fundamental misunderstandings in here. Need to verify this when I get a chance.
    if socket.type in ["VALUE", "INT"]:
        return fix(socket.default_value)
    if socket.type == "STRING":
        return str(socket.default_value)
    if socket.type in ["VECTOR", "RGBA"]:
        return "(" + ", ".join([fix(el) for el in socket.default_value]) + ")"
    if socket.type in ["SHADER", "OBJECT", "IMAGE", "TEXTURE", "MATERIAL", "COLLECTION"]:
        return socket.type.title() + ": " + socket.default_value.name
    if socket.type == "BOOLEAN":
        return "True" if socket.default_value else "False"
    return unprintable


def get_value_types(socket: NodeSocket) -> list[str]:
    types = {
        "INT": ["int"],
        "VALUE": ["float"],
        "VECTOR": ["float", "float", "float"],
        "ROTATION": ["float", "float", "float", "float"],
        "RGBA": ["float", "float", "float", "float"],
        "BOOLEAN": ["bool"]
    }
    for t in ["STRING", "SHADER", "OBJECT", "IMAGE", "TEXTURE", "MATERIAL", "COLLECTION"]:
        types[t] = ["string"]
    return types[socket.type] if socket.type in types else []


def can_value_numeric_compare(socket: NodeSocket):
    return socket.type in ["INT", "VALUE", "VECTOR", "RGBA"]


@dataclass
class ExplanationState():
    can_explain: bool = False
    has_explained: bool = False
    has_unexplained: bool = False


def get_node_explanation_state(node: Node | None) -> ExplanationState:
    node_state = ExplanationState()
    if not node:
        return node_state
    for socket in node.inputs:
        if socket.hide_value or socket.type == "CUSTOM" or not socket.enabled:
            continue
        node_state.can_explain = True
        if hasattr(socket, "tmy_explanation"):
            if socket.tmy_explanation.active:
                node_state.has_explained = True
            else:
                node_state.has_unexplained = True
        if node_state.has_explained and node_state.has_unexplained:
            return node_state
    return node_state
