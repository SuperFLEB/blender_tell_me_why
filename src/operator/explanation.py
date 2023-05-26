import bpy
from typing import Set
from bpy.types import Operator
from bpy.props import IntProperty

if "_LOADED" in locals():
    import importlib

    for mod in ():  # list all imports here
        importlib.reload(mod)
_LOADED = True


def get_default_explanation():
    return {
        "description": "(No Explanation)",
        "value": None,
        "formula": None,
    }


class CreateExplanation(Operator):
    """Initialize Tell Me Why data for a given node"""
    bl_idname = "tell_me_why.create_explanation"
    bl_label = "Create Tell Me Why Explanation"
    bl_options = {'UNDO'}
    input_socket_index: IntProperty(
        name="input_socket_index",
        default=0
    )

    def execute(self, context) -> Set[str]:
        node = context.active_node
        node_explanation: list[dict] = node['explanation'] if 'explanation' in node else [{} for socket in node.inputs]
        node_explanation[self.input_socket_index] = get_default_explanation()
        node['explanation'] = node_explanation
        return {'FINISHED'}


class RemoveExplanation(Operator):
    """Initialize Tell Me Why data for a given node"""
    bl_idname = "tell_me_why.remove_explanation"
    bl_label = "Remove Tell Me Why Explanation"
    bl_options = {'UNDO'}
    input_socket_index: IntProperty(
        name="input_socket_index",
        default=0
    )

    def execute(self, context) -> Set[str]:
        node = context.active_node
        node_explanation: list[dict] = node['explanation'] if 'explanation' in node else [{} for socket in node.inputs]
        node_explanation[self.input_socket_index] = {}
        node['explanation'] = node_explanation
        return {'FINISHED'}


REGISTER_CLASSES = [CreateExplanation, RemoveExplanation]
