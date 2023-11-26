import bpy
from ..props import variable as variable_props
from ..lib import pkginfo, addon as addon_lib, variable as variable_lib, util
from ..operator import variable as variable_op
from . import n_panel, ul_variables, variables as variables_panel

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, variable_props, addon_lib, variable_lib, util, n_panel):
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()

def get_location(self):
    return self.get("value", 0)


def set_location(self, value):
    changed = self.get("value", 0) != value
    self["value"] = value
    if changed:
        n_panel.update_panel_category()


class TMYPrefsPanel(bpy.types.AddonPreferences):
    bl_idname = package_name

    start_expanded: bpy.props.BoolProperty(
        name="Always show all sockets",
        description="Show sockets you have not added explanations to when viewing a node, without needing to click "
                    '"Show All/Add More"',
        default=False
    )

    n_panel_location: bpy.props.EnumProperty(
        name="N-Panel location",
        description="Where should the Tell Me Why panel be located?",
        items=[
            ("Tell Me Why", 'In a "Tell Me Why" tab', "Put the panel in its own tab"),
            ("Node", 'In the "Node" tab', "Put the panel after other items in the Node tab"),
        ],
        get=get_location,
        set=set_location
    )

    global_variables_library: bpy.props.CollectionProperty(type=variable_props.TMYVariable)

    def draw(self, context) -> None:
        layout = self.layout
        layout.prop(self, "start_expanded")
        layout.prop(self, "n_panel_location")

        tmy = context.window_manager.tell_me_why_globals

        list_box = layout.box()
        list_box.label(text="Variable Library:")

        doc_layout = list_box.column()
        doc_layout.scale_y = 0.5
        import_menu_label = variables_panel.TMY_MT_ImportVariables.bl_label
        doc_layout.label(text="Your Variable Library is a place for commonly-used variables that can be easily imported into Scenes.")
        doc_layout.label(text=f"To use Variable Library variables, import them into a Scene using the \"{import_menu_label}\" feature of the Tell Me Why panel.")

        list_row = list_box.row()
        list_col = list_row.column()

        list_col.template_list(
            ul_variables.TMY_UL_Variables.bl_idname,
            "global_variables_library_list",
            self, "global_variables_library",
            tmy, "variable_selected_index_prefs"
        )

        variables = self.global_variables_library
        if variables and variables[tmy.variable_selected_index_prefs]:
            edit_box = list_col.box()
            edit_box.prop(variables[tmy.variable_selected_index_prefs], "name")
            edit_box.prop(variables[tmy.variable_selected_index_prefs], "formula", text="Value")

        ops_col = list_row.column(align=True)
        ops_col.operator(variable_op.AddGlobalLibVariable.bl_idname, icon='ADD', text="")
        ops_col.operator(variable_op.RemoveGlobalLibVariable.bl_idname, icon='REMOVE', text="")


REGISTER_CLASSES = [TMYPrefsPanel]
