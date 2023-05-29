import bpy
from bpy.types import Panel
from ..operator import explanation as explanation_operators
from ..lib import node as node_lib
from ..lib import formula as formula_lib

if "_LOADED" in locals():
    import importlib

    for mod in (explanation_operators, node_lib, formula_lib):  # list all imports here
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

        for socket in [s for s in node.inputs if is_socket_explainable(s)]:
            explanation = socket.explanation
            socket_layout = layout.column()
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
                                    match = formula_lib.does_value_equal_formula_result(component_current_value, component.formula)
                                    component_layout.label(text="Value OK" if match else "Value Not Updated")
                                except formula_lib.FormulaExecutionException as e:
                                    component_layout.label(text="Formula error")
                            else:
                                component_layout.label(text="No formula or noted value")
                        else:
                            component_layout.label(text=f"{component_current_value}")

                else:
                    socket_layout.operator(explanation_operators.CreateSocketExplanation.bl_idname,
                                           text=f"Explain {socket.name}")


REGISTER_CLASSES = [TellMeWhyNPanel]
