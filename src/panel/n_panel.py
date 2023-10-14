import bpy
from bpy.types import Panel, UILayout, NodeSocket, NodeInternal
from ..operator import explanation as explanation_op
from ..lib import pkginfo, util, node as node_lib, formula as formula_lib, addon as addon_lib, \
    explanation as explanation_lib
from ..props import explanation as explanation_props

package_name = pkginfo.package_name()
icon_value = addon_lib.icon_value

if 1 or "_LOADED" in locals():
    import importlib

    for mod in (explanation_op, node_lib, formula_lib, addon_lib, util, explanation_lib):  # list all imports here
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
    "formula": "icon_formula",
    "bad_formula": "ERROR",
    "mismatch": "icon_not_equal",
    "node_value": "NODE",
    "remove": "X",
    "security": "DECORATE_LOCKED"
}

# Do NOT use this for anything except equality checking!
last_seen_node = None


class TellMeWhyPanel(Panel):
    bl_idname = "NODE_PT_tell_me_why"
    bl_category = "Tell Me Why"
    bl_label = "Tell Me Why"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    def disregard_node(self, context, layout: bpy.types.UILayout, node: bpy.types.NodeInternal):
        if not (node and node.select):
            layout.label(text="No node selected")
            return True

        if not getattr(node, "inputs", None):
            layout.label(text="Node has no inputs")
            return True

        return False

    def draw_socket_title(self, context, socket, socket_state, layout: UILayout, edit_mode: bool = False):
        socket_title_layout = layout.row()

        socket_title_layout.prop(data=socket_state, property="edit_mode", text="", icon=icons["edit_mode"])
        socket_title_layout.label(text=socket.name)

        # Only make the socket removable in view mode. This might seem a bit odd, but the "X" looks like a close
        # button, and it's too easy to accidentally clobber your whole socket setup by hitting X instead of the pencil
        if not edit_mode:
            socket_title_layout.operator(explanation_op.RemoveSocketExplanation.bl_idname,
                                         icon=icons["remove"], text="", emboss=False)

        if edit_mode:
            layout.prop(data=socket.explanation, property="description", text="", icon=icons["description"])
        elif socket.explanation.description:
            addon_lib.multiline_label(context, layout, text=socket.explanation.description, icon=icons["description"])

    def draw_unexplained_socket(self, context, layout, socket):
        layout.context_pointer_set(name="operator_socket", data=socket)

        layout.operator(
            explanation_op.CreateSocketExplanation.bl_idname,
            text="",
            icon=icons["add"]
        )
        layout.label(text=socket.name)
        if hasattr(socket, "default_value"):
            layout.label(text=util.format_prop_value(socket.default_value))

    def draw_split_components_button(self, context, layout: UILayout, socket: NodeSocket,
                                     explanation: explanation_props.Explanation,
                                     edit_mode: bool):
        """Draw the "Split Components" button if one is necessary"""

        if not (len(node_lib.get_value_types(socket)) < 1 and edit_mode):
            return

        abbr_map = {
            socket.type: "",
            "VECTOR": "XYZ",
            "RGBA": "RGBA"
        }

        label = f"Split {abbr_map[socket.type]} Components"
        layout.prop(data=explanation, property="split_components", text=label, toggle=True)

    def get_component_labels(self, context, socket, explanation) -> list[str | tuple[str]]:
        if not explanation.split_components:
            return [f"{socket.name} ({node_lib.socket_type_label(socket)})"]

        label_map = {
            "VECTOR": "XYZ",
            "RGBA": ("Red", "Green", "Blue", "Alpha")
        }.get(socket.type, None) or [f"{socket.name} ({node_lib.socket_type_label(socket)})"]


        return [str(lbl) for lbl in label_map]

    def draw_socket_explanation(self, context, layout: UILayout, socket: NodeSocket,
                                socket_index: int, tmy):

        # Skip hidden and valueless sockets
        if not is_socket_explainable(socket):
            return

        # Socket w/o active explanation: Show name and value
        if not (hasattr(socket, "explanation") and socket.explanation.active):
            self.draw_unexplained_socket(context, layout.row(), socket)
            return

        explanation = socket.explanation
        socket_state = tmy.socket_states[socket_index]
        edit_mode = socket_state["edit_mode"]


        # Active Socket

        ## Socket Layout
        socket_layout = layout.box()
        socket_layout.context_pointer_set(name="operator_socket", data=socket)

        self.draw_socket_title(context, socket, tmy.socket_states[socket_index], socket_layout, edit_mode)

        # If the socket has no values, we can't set formulas, so skip that whole part
        if not hasattr(socket, "default_value"):
            return

        self.draw_split_components_button(context, socket_layout, socket, explanation, edit_mode)

        components = explanation.components if explanation.split_components else [explanation.components[0]]
        component_labels = self.get_component_labels(context, socket, explanation)
        evaluated = explanation_lib.Evaluation(socket)

        for c_idx, component in enumerate(components):
            component_layout = socket_layout.box()
            component_layout.scale_y = 1 if edit_mode else 0.8

            if edit_mode or len(explanation.components) > 1:
                component_layout.label(text=component_labels[c_idx])

            component_current_value = socket.default_value[
                c_idx] if explanation.split_components else socket.default_value
            component_formula = component.formula if component.use_formula else component_current_value

            if edit_mode:
                component_layout.prop(data=component, property="description", text="", icon=icons["description"])
            elif component.description:
                addon_lib.multiline_label(context, component_layout, text=component.description,
                                          icon=icons["description"])

            if edit_mode:
                formula_layout = component_layout.split(factor=0.2, align=True)
                formula_layout.prop(data=component, property="use_formula", text="",
                                    icon_value=icon_value(icons["formula"]))

                if component.use_formula:
                    formula_layout.prop(data=component, property="formula", text="")
                    result_layout = component_layout.column(align=True)

                    if evaluated.is_error(c_idx):
                        result_layout.label(icon=icons["error"], text="Missing/Invalid Formula")
                    elif evaluated.is_index_matching(c_idx):
                        result_layout.label(icon=icons["check"], text="Value Applied")
                    else:
                        result_layout.label(icon_value=icon_value(icons["mismatch"]), text="Value Not Applied")
                else:
                    formula_layout.label(text=util.format_prop_value(component_current_value))
            else:
                if not component.use_formula:
                    icon_id = icons["node_value"]
                elif evaluated.is_error(c_idx):
                    icon_id = icons["bad_formula"]
                elif evaluated.is_index_matching(c_idx):
                    icon_id = icons["formula"]
                else:
                    icon_id = icons["mismatch"]

                component_layout.label(text=util.format_prop_value(component_formula), icon_value=icon_value(icon_id))

            if not evaluated.is_index_matching(c_idx) and not evaluated.is_error(c_idx):
                component_layout.context_pointer_set(name="operator_socket", data=socket)
                apply_operator = component_layout.operator(
                    explanation_op.ApplyFormula.bl_idname,
                    text="Apply",
                )
                apply_operator.component_index = c_idx

        has_rgba_formulas = False

        # Create the color swatch
        if has_rgba_formulas and not evaluated.has_errors():
            socket_state.rgba = evaluated.get_results()
            socket_color_layout = socket_layout.row(align=True)
            socket_color_layout.label(text="", icon=icons["check"] if evaluated.is_matching() else icons["error"])
            socket_color_layout.prop(text="", data=socket_state, property="rgba")
            socket_color_layout.prop(text="", data=socket, property="default_value")

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        tmy = wm.tell_me_why_globals
        prefs = bpy.context.preferences.addons[package_name].preferences
        node = context.active_node

        if self.disregard_node(context, layout, node):
            return

        # If the node selection has changed, reset the WindowManager stored node/socket info
        # (Ephemeral display info is stored in WindowManager to not clutter the file)
        global last_seen_node
        if node != last_seen_node:
            last_seen_node = node
            tmy.socket_states.clear()
            tmy.show_unexplained = prefs.start_expanded
            for socket in node.inputs:
                socket_state = tmy.socket_states.add()
                socket_state["edit_mode"] = False

        # If there are no explained sockets, hard-True "show_all" so the user sees the "Add" buttons
        has_explained_sockets = False

        socket: NodeSocket
        for socket in node.inputs:
            if is_socket_explainable(socket) and hasattr(socket, "explanation") and socket.explanation.active:
                has_explained_sockets = True
                layout.prop(data=tmy, property="show_unexplained", text="Show All / Add More", toggle=True)
                break
        show_all = tmy.show_unexplained or not has_explained_sockets

        socket: NodeSocket
        for s_idx, socket in enumerate(node.inputs):
            # Hide inactive sockets unless show_all is set
            if not (show_all or (hasattr(socket, "explanation") and socket.explanation.active)):
                continue
            self.draw_socket_explanation(context, layout, socket, s_idx, tmy)


def set_panel_category_from_prefs():
    """Set the panel's category (tab) from the n_panel_location preference"""
    try:
        location = bpy.context.preferences.addons[package_name].preferences.n_panel_location
        TellMeWhyPanel.bl_category = location
    except AttributeError:
        # This means the preferences aren't set up, so just pass and use the default
        pass


def update_panel_category():
    """Set the panel's category (tab) from the n_panel_location preference and unregister/reregister the panel"""
    bpy.utils.unregister_class(TellMeWhyPanel)
    set_panel_category_from_prefs()
    bpy.utils.register_class(TellMeWhyPanel)


REGISTER_CLASSES = [TellMeWhyPanel]
