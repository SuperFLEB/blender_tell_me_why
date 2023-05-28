import bpy
from bpy.types import Panel
from ..operator import explanation as explanation_operators
from ..lib import node as node_lib

if "_LOADED" in locals():
    import importlib

    for mod in (explanation_operators, node_lib):  # list all imports here
        importlib.reload(mod)
_LOADED = True


def is_socket_explainable(input):
    if not input.enabled:
        return False
    if input.type == "CUSTOM":
        return False
    return True


class TellMeWhyNPanel(Panel):
    bl_idname = 'NODE_PT_tell_me_why'
    bl_category = 'Tell Me Why'
    bl_label = 'Tell Me Why'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        node = context.active_node
        if not (node and node.select):
            layout.label(text="No node selected")
            return

        explanation = node['explanation'] if 'explanation' in node else [{} for n in node.inputs]

        for socket in [s for s in node.inputs if is_socket_explainable(s)]:
            col = layout.column()
            col.context_pointer_set(name='operator_socket', data=socket)
            if hasattr(socket, 'explanation'):
                if socket.explanation.active:
                    col.operator(explanation_operators.RemoveSocketExplanation.bl_idname, text=f"Remove Explnation")
                    col.prop(data=socket.explanation, property="description")
                    col.prop(data=socket.explanation, property="formula")
                else:
                    col.operator(explanation_operators.CreateSocketExplanation.bl_idname, text=f"Explain {socket.name}")


REGISTER_CLASSES = [TellMeWhyNPanel]
