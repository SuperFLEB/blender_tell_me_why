import bpy
from bpy.types import Panel, Menu, UIList
from . import ul_variables
from ..lib import pkginfo, addon as addon_lib, variable as variable_lib, formula as formula_lib
from ..operator import variable as variable_op

package_name = pkginfo.package_name()

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, addon_lib, variable_op, formula_lib):
        importlib.reload(mod)
_LOADED = True


class TMY_MT_ImportVariables(Menu):
    bl_idname = 'TMY_MT_import_variables'
    bl_label = 'Import Variables From...'

    def draw(self, context):
        layout = self.layout
        for scene in bpy.data.scenes:
            if scene != context.scene:
                oper = layout.operator(variable_op.ImportVariablesFromScene.bl_idname, text=scene.name)
                oper.scene = scene.name

class NODE_PT_TMYFileVariables(Panel):
    bl_idname = "NODE_PT_tmy_file_variables"
    bl_category = "Tell Me Why"
    bl_label = "Scene Variables"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    variable_selected_index = 0

    def draw(self, context):
        layout = self.layout
        list_row = layout.row()

        tmy = context.window_manager.tell_me_why_globals
        pointer = variable_lib.get_variables_pointer()

        list_col = list_row.column()
        list_col.template_list(ul_variables.TMY_UL_Variables.bl_idname, "variables_list", pointer[0], pointer[1],
                               tmy, "variable_selected_index")

        variables = variable_lib.get_variables()
        if variables and variables[tmy.variable_selected_index]:
            edit_box = list_col.box()
            edit_box.prop(variables[tmy.variable_selected_index], "name")
            edit_box.prop(variables[tmy.variable_selected_index], "formula", text="Value")

        ops_col = list_row.column(align=True)
        ops_col.operator("tell_me_why.add_scene_variable", icon='ADD', text="")
        ops_col.operator("tell_me_why.remove_scene_variable", icon='REMOVE', text="")

        layout.menu(TMY_MT_ImportVariables.bl_idname)

        if len(bpy.data.scenes) > 1:
            scene_box = layout.box()
            addon_lib.multiline_label(context, scene_box,
                                      "You have multiple Scenes in this document. Variables are set per-scene, so you "
                                      "may need to import them from another Scene in order for all formulas "
                                      "to function.", icon="INFO")


REGISTER_CLASSES = [NODE_PT_TMYFileVariables, TMY_MT_ImportVariables]
