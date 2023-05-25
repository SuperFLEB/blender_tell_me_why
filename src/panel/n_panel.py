import bpy
from bpy.types import Panel
from ..operator import explanation as explanation_operators
from ..lib import node as node_lib

if "_LOADED" in locals():
    import importlib

    for mod in (explanation_operators, node_lib):  # list all imports here
        importlib.reload(mod)
_LOADED = True


def filter_inputs(inputs):
    return [input for input in inputs if input.enabled]


class TellMeWhyNPanel(Panel):
    bl_idname = 'NODE_PT_tell_me_why'
    bl_category = 'Tell Me Why'
    bl_label = 'Tell Me Why'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        node = context.active_node

        explanation = node['explanation'] if 'explanation' in node else [{} for node in node.inputs]

        for index, socket in enumerate(filter_inputs(node.inputs)):
            layout.label(text=f"{socket.name}: {node_lib.default_value_string(socket)}")
            socket_layout = layout.column(heading=socket.name)

            if explanation[index]:
                socket_layout.label(text=explanation[index]['description'])
                create_button = socket_layout.operator(explanation_operators.RemoveExplanation.bl_idname)
                create_button.input_socket_index = index
            else:
                socket_layout.label(text='No explanation')
                create_button = socket_layout.operator(explanation_operators.CreateExplanation.bl_idname)
                create_button.input_socket_index = index


REGISTER_CLASSES = [TellMeWhyNPanel]
