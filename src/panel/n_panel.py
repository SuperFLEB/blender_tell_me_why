import bpy
from bpy.types import Panel
from ..operator import explanation as explanation_operators
from ..lib import node as node_lib
from ..lib import formula as formula_lib
from ..lib import trust as trust_lib
from ..lib import util

if "_LOADED" in locals():
    import importlib

    for mod in (explanation_operators, node_lib, formula_lib, trust_lib, util):  # list all imports here
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

        if not getattr(node, 'inputs', None):
            layout.label(text="Node has no inputs")
            return

        if not trust_lib.is_trustable_node(node):
            message_layout = layout.column()
            message_layout.scale_y = 0.7
            for line in util.wordwrap("This node type is not supported by the Tell Me Why addon. Consider raising an issue on the project page. See the support link in the addon's Preferences panel.", 45):
                message_layout.label(text=line)
            message_layout.label(text=f"({node.type} in {context.space_data.tree_type} failed is_trustable_node)")
            return

        for socket in [s for s in node.inputs if is_socket_explainable(s)]:
            explanation = socket.explanation
            socket_layout = layout.box()
            socket_layout.context_pointer_set(name='operator_socket', data=socket)
            if hasattr(socket, 'explanation'):
                if explanation.active:
                    component_count = len(node_lib.get_value_types(socket))
                    socket_layout.operator(explanation_operators.RemoveSocketExplanation.bl_idname,
                                           text=f"Remove Explnation")
                    socket_layout.prop(data=explanation, property="description")

                    if component_count > 1:
                        socket_layout.prop(data=explanation, property='split_components')

                    if explanation.split_components:
                        components = explanation.components
                        component_labels = {
                            socket.type: ["" for c in explanation.components],
                            'VECTOR': 'XYZ',
                            'RGBA': ('Red', 'Green', 'Blue', 'Alpha')
                        }[socket.type]
                        component_labels = [f"{socket.name} {lbl}" if lbl else socket.name for lbl in component_labels]
                    else:
                        component_labels = [socket.name]
                        components = [explanation.components[0]]

                    for idx, component in enumerate(components):
                        component_layout = socket_layout.column()
                        component_layout.label(text=component_labels[idx])
                        component_layout.prop(data=component, property="description")

                        # TODO FIX: Should also use split_components
                        component_current_value = socket.default_value[
                            idx] if component_count > 1 else socket.default_value

                        component_layout.prop(data=component, property="use_formula")

                        if component.use_formula:
                            component_layout.prop(data=component, property="formula")
                            if component.formula:
                                match = False
                                try:
                                    result = formula_lib.exec_formula(component.formula, node)
                                    match = formula_lib.does_value_equal_formula_result(component_current_value, component.formula)
                                    component_layout.label(text="Value OK" if match else "Value Not Updated")
                                except formula_lib.FormulaExecutionException as e:
                                    component_layout.label(text=f"Formula error")
                            else:
                                component_layout.label(text="No formula or noted value")
                        else:
                            component_layout.label(text=f"{component_current_value}")

                else:
                    socket_layout.operator(explanation_operators.CreateSocketExplanation.bl_idname,
                                           text=f"Explain {socket.name}")


REGISTER_CLASSES = [TellMeWhyNPanel]
