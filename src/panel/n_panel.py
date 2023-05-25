import bpy
from bpy.types import Panel
from ..operator import explanation as explanation_operators

if "_LOADED" in locals():
    import importlib

    for mod in ():  # list all imports here
        importlib.reload(mod)
_LOADED = True


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

        for index, socket in enumerate(node.inputs):
            layout.label(text=f"{socket.name}: {socket.default_value}")
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
