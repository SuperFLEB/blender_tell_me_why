import bpy
from bpy.types import Panel, UILayout, NodeSocket

from ..lib import pkginfo, util, node as node_lib, formula as formula_lib, addon as addon_lib, \
    evaluation as evaluation_lib
from ..operator import explanation as explanation_op

package_name = pkginfo.package_name()
icon_value = addon_lib.icon_value

if "_LOADED" in locals():
    import importlib

    for mod in (explanation_op, node_lib, formula_lib, addon_lib, util, evaluation_lib):  # list all imports here
        importlib.reload(mod)
_LOADED = True


def is_socket_explainable(input: NodeSocket):
    return input.enabled and not (input.hide_value or input.type == "CUSTOM")


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

    def _node_invalid_label(self, node: bpy.types.NodeInternal) -> str | None:
        """Return the reason if the node is invalid, otherwise None"""

        if not (node and node.select):
            return "No node selected"

        if not getattr(node, "inputs", None):
            return "Node has no inputs"

        return

    def _draw_socket_title(self, context, socket, socket_state, layout: UILayout, edit_mode: bool = False) -> None:
        """Draw the socket title, including the Remove and Edit icons"""

        socket_title_layout = layout.row()

        socket_title_layout.prop(data=socket_state, property="edit_mode", text="", icon=icons["edit_mode"])
        socket_title_layout.label(text=socket.name)

        # Only make the socket removable in view mode. This might seem a bit odd, but the "X" looks like a close
        # button, and it's too easy to accidentally clobber your whole socket setup by hitting X instead of the pencil
        if not edit_mode:
            socket_title_layout.operator(explanation_op.RemoveSocketExplanation.bl_idname,
                                         icon=icons["remove"], text="", emboss=False)

    def _draw_unexplained_socket(self, context, layout, socket):
        """Draw the view for a socket that has no annotations. Includes the "Add" button and the value."""

        layout.context_pointer_set(name="operator_socket", data=socket)
        layout.operator(
            explanation_op.CreateSocketExplanation.bl_idname,
            text="",
            icon=icons["add"]
        )
        layout.label(text=socket.name)
        if hasattr(socket, "default_value"):
            layout.label(text=util.format_prop_value(socket.default_value))

    def _get_component_labels(self, socket: NodeSocket) -> tuple[str]:
        """Return a tuple of labels for socket value components"""
        explanation = socket.tmy_explanation
        if not explanation.split_components:
            return (f"{socket.name} ({node_lib.socket_type_label(socket)})",)

        labels = {
                     "VECTOR": ("X", "Y", "Z"),
                     "ROTATION": ("W", "X", "Y", "Z"),
                     "RGBA": ("Red", "Green", "Blue", "Alpha")
                 }.get(socket.type, None) or tuple([f"{socket.name} {i}" for i, _ in explanation.components])

        return labels

    def _draw_socket_explanation(self, context, layout: UILayout, socket: NodeSocket,
                                 socket_index: int, tmy):

        # Skip hidden and valueless sockets
        if not is_socket_explainable(socket):
            return

        # Socket w/o active explanation: Show name and value
        if not (hasattr(socket, "tmy_explanation") and socket.tmy_explanation.active):
            self._draw_unexplained_socket(context, layout.row(), socket)
            return

        explanation = socket.tmy_explanation
        socket_state = tmy.socket_states[socket_index]
        edit_mode = socket_state["edit_mode"]

        socket_layout = layout.box()
        socket_layout.context_pointer_set(name="operator_socket", data=socket)

        self._draw_socket_title(context, socket, tmy.socket_states[socket_index], socket_layout, edit_mode)

        if edit_mode:
            socket_layout.prop(data=socket.tmy_explanation, property="description", text="", icon=icons["description"])
        elif socket.tmy_explanation.description:
            addon_lib.multiline_label(context, socket_layout, text=socket.tmy_explanation.description,
                                      icon=icons["description"])

        # If the socket has no values, we can't set formulas, so only display annotation
        if not hasattr(socket, "default_value"):
            return

        if edit_mode and len(node_lib.get_value_types(socket)) > 1:
            abbr_map = {
                socket.type: "",
                "VECTOR": "XYZ",
                "RGBA": "RGBA"
            }
            label = f"Split {abbr_map[socket.type]} Components"
            socket_layout.prop(data=explanation, property="split_components", text=label, toggle=True)

        components = explanation.components if explanation.split_components else [explanation.components[0]]
        component_labels = self._get_component_labels(socket)
        evaluated = evaluation_lib.Evaluation(socket)
        for c_idx, component in enumerate(components):
            self._draw_component_edit(socket_layout, socket, evaluated, c_idx, component,
                                      component_labels[c_idx]) if edit_mode else self._draw_component_view(
                context, socket_layout, socket, evaluated, c_idx, component, component_labels[c_idx])

    def _draw_component_view(self, context, layout, socket, evaluated, index, component, label):
        explanation = socket.tmy_explanation
        component_layout = layout.box()
        component_layout.scale_y = 0.8

        if explanation.split_components and len(explanation.components) > 1:
            component_layout.label(text=label)

        if component.description:
            addon_lib.multiline_label(context, component_layout, text=component.description, icon=icons["description"])

        if not component.use_formula:
            icon_id = icons["node_value"]
        elif evaluated.is_error(index):
            icon_id = icons["bad_formula"]
        elif evaluated.is_index_matching(index):
            icon_id = icons["formula"]
        else:
            icon_id = icons["mismatch"]

        component_current_value = socket.default_value[index] if explanation.split_components else socket.default_value
        component_formula = component.formula if component.use_formula else component_current_value
        component_layout.label(text=util.format_prop_value(component_formula), icon_value=icon_value(icon_id))

        if not evaluated.is_index_matching(index) and not evaluated.is_error(index):
            component_layout.context_pointer_set(name="operator_socket", data=socket)
            apply_operator = component_layout.operator(
                explanation_op.ApplyFormula.bl_idname,
                text="Apply",
            )
            apply_operator.component_index = index

    def _draw_component_edit(self, layout, socket, evaluated, index, component, label):
        explanation = socket.tmy_explanation
        component_layout = layout.box()
        component_layout.scale_y = 1

        component_layout.label(text=label)

        component_current_value = socket.default_value[
            index] if explanation.split_components else socket.default_value

        component_layout.prop(data=component, property="description", text="", icon=icons["description"])

        formula_layout = component_layout.split(factor=0.2, align=True)

        formula_layout.prop(data=component, property="use_formula", text="", icon_value=icon_value(icons["formula"]))

        if component.use_formula:
            formula_layout.prop(data=component, property="formula", text="")
            result_layout = component_layout.column(align=True)

            if evaluated.is_error(index):
                result_layout.label(icon=icons["error"], text="Missing/Invalid Formula")
            elif evaluated.is_index_matching(index):
                result_layout.label(icon=icons["check"], text="Value Applied")
            else:
                result_layout.label(icon_value=icon_value(icons["mismatch"]), text="Value Not Applied")

                component_layout.context_pointer_set(name="operator_socket", data=socket)
                apply_operator = component_layout.operator(
                    explanation_op.ApplyFormula.bl_idname,
                    text="Apply",
                )
                apply_operator.component_index = index
        else:
            formula_layout.label(text=util.format_prop_value(component_current_value))

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        tmy = wm.tell_me_why_globals
        prefs = bpy.context.preferences.addons[package_name].preferences
        node = context.active_node

        if invalid_label := self._node_invalid_label(node):
            layout.label(text=invalid_label)
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

        has_explained_sockets = False
        has_unexplained_sockets = False

        socket: NodeSocket
        for socket in node.inputs:
            if is_socket_explainable(socket) and hasattr(socket, "tmy_explanation"):
                if socket.tmy_explanation.active:
                    has_explained_sockets = True
                else:
                    has_unexplained_sockets = True
            if has_unexplained_sockets and has_explained_sockets:
                break

        if has_unexplained_sockets:
            su_label = "Hide Inactive" if tmy.show_unexplained else "Show All"
            layout.prop(data=tmy, property="show_unexplained", text=su_label, toggle=True)

        if not has_explained_sockets and not tmy.show_unexplained:
            addon_lib.multiline_label(context, layout, text="No active annotations. Use \"Show All\" to add some.")

        socket: NodeSocket
        for s_idx, socket in enumerate(node.inputs):
            # Hide inactive sockets unless show_all is set
            if not (tmy.show_unexplained or (hasattr(socket, "tmy_explanation") and socket.tmy_explanation.active)):
                continue
            self._draw_socket_explanation(context, layout, socket, s_idx, tmy)


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
