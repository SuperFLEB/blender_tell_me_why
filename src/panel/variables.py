import bpy
from bpy.types import Panel, UIList
from ..lib import pkginfo, variable as variable_lib

package_name = pkginfo.package_name()

if "_LOADED" in locals():
    import importlib
    for mod in (pkginfo, variable_lib):  # list all imports here
        importlib.reload(mod)
_LOADED = True


class TMY_UL_variables(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        split = layout.row()
        split.label(text=item.name)
        split.label(text=item.formula)


class TellMeWhyFileVariablesPanel(Panel):
    bl_idname = "NODE_PT_tmy_file_variables"
    bl_category = "Tell Me Why"
    bl_label = "Variables"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    variable_selected_index = 0

    def draw(self, context):
        layout = self.layout
        tmy = context.window_manager.tell_me_why_globals
        pointer = variable_lib.get_variables_pointer()

        list_row = layout.row()

        list_col = list_row.column()
        list_col.template_list("TMY_UL_variables", "variables_list", pointer[0], pointer[1], tmy, "variable_selected_index")

        variables = variable_lib.get_variables()
        if variables and variables[tmy.variable_selected_index]:
            edit_box = list_col.box()
            edit_box.prop(variables[tmy.variable_selected_index], "name")
            edit_box.prop(variables[tmy.variable_selected_index], "formula", text="Value")

        ops_col = list_row.column(align=True)
        ops_col.operator("tell_me_why.add_scene_variable", icon='ADD', text="")
        ops_col.operator("tell_me_why.remove_scene_variable", icon='REMOVE', text="")

REGISTER_CLASSES = [TMY_UL_variables, TellMeWhyFileVariablesPanel]
