import bpy
from bpy.types import Panel, UILayout, NodeSocket, NodeInternal
from ..operator import explanation as explanation_op
from ..lib import node as node_lib
from ..lib import formula as formula_lib
from ..lib import trust as trust_lib
from ..lib import util

if "_LOADED" in locals():
    import importlib

    for mod in (explanation_op, node_lib, formula_lib, trust_lib, util):  # list all imports here
        importlib.reload(mod)
_LOADED = True


def is_socket_explainable(input):
    if not input.enabled:
        return False
    if input.type == "CUSTOM":
        return False
    return True


icons = {
    "add": "ADD",
    "check": "CHECKMARK",
    "description": "INFO",
    "edit_mode": "GREASEPENCIL",
    "error": "ERROR",
    "formula": "DRIVER_TRANSFORM",
    "node_value": "NODE",
    "remove": "X",
}


# Do NOT use this for anything except equality checking!
last_seen_node = None


class TellMeWhyNPanel(Panel):
    bl_idname = 'NODE_PT_tell_me_why'
    bl_category = 'Tell Me Why'
    bl_label = 'Tell Me Why'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'

    def ml_label(self, context, layout: bpy.types.UILayout=None, text: str=None, icon: str=None, omit_empty: bool = False) -> None:
        if omit_empty and not text:
            return
        blank_icon = {"icon": "BLANK1"} if icon else {}
        icon = {"icon": icon} if icon else {}

        container = layout.column()
        container.scale_y = 0.8
        lines = util.wordwrap(text, context.region.width / 10)
        container.label(text=lines[0], **icon)
        for line in lines[1:]:
            lbl = container.label(text=line, **blank_icon)

    def disregard_node(self, context, layout: bpy.types.UILayout, node: bpy.types.NodeInternal):
        if not (node and node.select):
            layout.label(text="No node selected")
            return True

        if not getattr(node, 'inputs', None):
            layout.label(text="Node has no inputs")
            return True

        if not trust_lib.is_trustable_node(node):
            message_layout = layout.column()
            message_layout.scale_y = 0.7
            for line in util.wordwrap("This node type is not supported by the Tell Me Why addon. Consider raising an issue on the project page. See the support link in the addon's Preferences panel.", 45):
                message_layout.label(text=line)
            message_layout.label(text=f"({node.type} in {context.space_data.tree_type} failed is_trustable_node)")
            return True

        return False

    def draw_socket_title(self, context, socket, socket_state, layout: UILayout, edit_mode: bool=False):
        socket_title_layout = layout.row()

        socket_title_layout.prop(data=socket_state, property="edit_mode", text="", icon=icons["edit_mode"])
        socket_title_layout.label(text=socket.name)
        socket_title_layout.operator(explanation_op.RemoveSocketExplanation.bl_idname,
                                     icon=icons["remove"], text="", emboss=False)
        if edit_mode:
            layout.prop(data=socket.explanation, property="description", text="", icon=icons["description"])
        elif socket.explanation.description:
            self.ml_label(context, layout, text=socket.explanation.description, icon=icons["description"])


    def draw_unexplained_socket(self, context, layout, socket):
        layout.context_pointer_set(name='operator_socket', data=socket)

        layout.operator(
            explanation_op.CreateSocketExplanation.bl_idname,
            text="",
            icon=icons['add']
        )
        layout.label(text=socket.name)
        if hasattr(socket, 'default_value'):
            layout.label(text=util.format_prop_value(socket.default_value))

    def draw_split_button(self, context, layout: UILayout, socket: NodeSocket, explanation: explanation_op.Explanation, edit_mode: bool):
        component_count = len(node_lib.get_value_types(socket))
        abbr_map = {
            socket.type: "",
            'VECTOR': 'XYZ',
            'RGBA': 'RGBA'
        }
        if component_count > 1 and edit_mode:
            label = f"Split {abbr_map[socket.type]} Components"
            layout.prop(data=explanation, property='split_components', text=label, toggle=True)

    def get_component_labels(self, context, socket, explanation) -> list[str | tuple[str]]:
        if explanation.split_components:
            label_map = {
                socket.type: [None for c in explanation.components],
                'VECTOR': 'XYZ',
                'RGBA': ('Red', 'Green', 'Blue', 'Alpha')
            }[socket.type]
            component_labels = [f"{lbl}" if lbl else socket.name for lbl in label_map]
            return component_labels
        else:
            return [f"{socket.name} ({node_lib.socket_type_label(socket)})"]

    def evaluate_socket_formulas(self, explanation, socket, node) -> list[dict[str, str]]:
        components = explanation.components if explanation.split_components else [explanation.components[0]]
        value_len = len(socket.default_value) if hasattr(socket.default_value, "__len__") else 1
        evaluations = []

        for c_idx, component in enumerate(components):
            value = socket.default_value[c_idx] if explanation.split_components else socket.default_value
            if not component.use_formula:
                evaluations.append({"value": value, "result": value, "match": True, "error": False})
                continue

            expect_len = 1 if explanation.split_components else value_len
            try:
                result = formula_lib.exec_formula(component.formula, node, expect_len=expect_len, extend_to_expected=True)
                error = False
            except formula_lib.FormulaExecutionException as e:
                evaluations.append({"value": value, "result": None, "match": False, "error": e})
                continue

            evaluations.append({"value": value, "result": result, "match": util.compare(value, result), "error": error})
        return evaluations


    def draw_socket_explanation(self, context, layout: UILayout, node: NodeInternal, socket: NodeSocket, socket_index: int, formulas_enabled: bool, tmy):
        explanation = socket.explanation
        socket_state = tmy.socket_states[socket_index]
        edit_mode = socket_state['edit_mode']

        # Skip hidden and valueless sockets
        if not is_socket_explainable(socket):
            return

        active_socket = hasattr(socket, 'explanation') and socket.explanation.active

        # Inactive socket: Show name and value
        if not active_socket:
            unexplained_socket_layout = layout.row()
            self.draw_unexplained_socket(context, unexplained_socket_layout, socket)
            return

        # Active Socket

        ## Socket Layout
        socket_layout = layout.box()
        socket_layout.context_pointer_set(name='operator_socket', data=socket)

        self.draw_socket_title(context, socket, tmy.socket_states[socket_index], socket_layout, edit_mode)

        # If the socket has no values, we can't set formulas, so skip that whole part
        if not hasattr(socket, 'default_value'):
            return

        self.draw_split_button(context, socket_layout, socket, explanation, edit_mode)
        components = explanation.components if explanation.split_components else [explanation.components[0]]
        component_labels = self.get_component_labels(context, socket, explanation)
        evaluations = self.evaluate_socket_formulas(explanation, socket, node)

        for c_idx, component in enumerate(components):
            component_layout = socket_layout.box()
            component_layout.scale_y = 1 if edit_mode else 0.8
            component_layout.label(text=component_labels[c_idx])
            comp_eval = evaluations[c_idx]
            component_current_value = socket.default_value[c_idx] if explanation.split_components else socket.default_value
            component_formula = component.formula if component.use_formula else component_current_value

            if edit_mode:
                component_layout.prop(data=component, property="description", text="", icon=icons["description"])
            elif component.description:
                self.ml_label(context, component_layout, text=component.description, icon=icons["description"])

            if edit_mode:
                formula_layout = component_layout.split(factor=0.2, align=True)
                formula_layout.prop(data=component, property="use_formula", text="", icon=icons["formula"])

                if component.use_formula:
                    formula_layout.prop(data=component, property="formula", text="")
                    result_layout = component_layout.column(align=True)
                    # result_layout.label(text="")

                    if component.formula and not comp_eval['error']:
                        if comp_eval['match']:
                            result_layout.label(icon=icons["check"], text="Value Applied")
                        else:
                            result_layout.label(icon=icons["error"], text="Value Not Applied")
                    else:
                        result_layout.label(icon=icons["error"], text="Invalid Formula")
                else:
                    formula_layout.label(text=util.format_prop_value(component_current_value))
            else:
                component_layout.label(text=util.format_prop_value(component_formula), icon=icons['formula'] if component.use_formula else icons['node_value'])

        has_rgba_formulas = False
        has_formula_errors = False
        rgba = [0, 0, 0, 0]

        if socket.type == 'RGBA' and formulas_enabled:
            if [ev for ev in evaluations if ev['error']]:
                has_formula_errors = True

            if explanation.split_components:
                rgba = list(socket.default_value)
                for c_idx, component in enumerate(components):
                    if component.use_formula:
                        has_rgba_formulas = True
                    rgba[c_idx] = evaluations[c_idx]['result']
            elif components[0].use_formula:
                has_rgba_formulas = True
                rgba = evaluations[0]['result']

        if has_rgba_formulas and not has_formula_errors:
            color_match = util.compare_vectors(socket_state.rgba, socket.default_value)
            print("RGBA?", rgba)
            socket_state.rgba = rgba
            socket_color_layout = socket_layout.row(align=True)
            socket_color_layout.label(text="", icon=icons['check'] if color_match else icons['error'])
            socket_color_layout.prop(text="", data=socket_state, property="rgba")
            socket_color_layout.prop(text="", data=socket, property="default_value")

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        tmy = wm.tell_me_why_globals
        node = context.active_node
        formulas_enabled = trust_lib.is_trusted()

        if self.disregard_node(context, layout, node):
            return

        # If the node selection has changed, reset the WindowManager stored node/socket info
        # (Ephemeral display info is stored in WindowManager to not clutter the file)
        global last_seen_node
        if node != last_seen_node:
            last_seen_node = node
            tmy.socket_states.clear()
            tmy.show_unexplained = False
            for socket in node.inputs:
                socket_state = tmy.socket_states.add()
                socket_state['edit_mode'] = False

        # If there are no explained sockets, hard-True "show_all" so the user sees the "Add" buttons
        has_explained_sockets = False
        for socket in node.inputs:
            if is_socket_explainable(socket) and hasattr(socket, 'explanation') and socket.explanation.active:
                has_explained_sockets = True
                layout.prop(data=tmy, property="show_unexplained", text="Show All / Add More", toggle=True)
                break
        show_all = tmy.show_unexplained or not has_explained_sockets

        for s_idx, socket in enumerate(node.inputs):
            # Hide inactive sockets unless show_all is set
            if not (show_all or (hasattr(socket, 'explanation') and socket.explanation.active)):
                continue
            self.draw_socket_explanation(context, layout, node, socket, s_idx, formulas_enabled, tmy)


REGISTER_CLASSES = [TellMeWhyNPanel]
