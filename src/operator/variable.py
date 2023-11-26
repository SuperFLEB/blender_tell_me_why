from typing import Set

import bpy
from bpy.types import Operator
from ..lib import variable as variable_lib
from ..lib import pkginfo

if "_LOADED" in locals():
    import importlib

    for mod in (variable_lib,):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()

class AddVariable(Operator):
    """Add a scene variable"""
    bl_idname = "tell_me_why.add_scene_variable"
    bl_label = "Add Scene Variable"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context) -> Set[str]:
        tmy = context.window_manager.tell_me_why_globals
        tmy.variable_selected_index = variable_lib.add()
        return {'FINISHED'}


class RemoveVariable(Operator):
    """Remove a scene variable"""
    bl_idname = "tell_me_why.remove_scene_variable"
    bl_label = "Remove Variable"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context) -> Set[str]:
        tmy = context.window_manager.tell_me_why_globals
        index = tmy.variable_selected_index
        variable_lib.remove(index)
        count = len(variable_lib.get_variables())
        if index >= count:
            tmy.variable_selected_index = count - 1
        return {'FINISHED'}


class ImportVariablesFromScene(Operator):
    """Import variables from the scene, overwriting current values if they exist"""
    bl_idname = "tell_me_why.import_variable_from_scene"
    bl_label = "(Invalid Scene)"
    bl_options = {'REGISTER', 'UNDO'}

    scene: bpy.props.StringProperty()

    def execute(self, context):
        if not self.scene or not self.scene in bpy.data.scenes or context.scene.name == self.scene:
            self.report({'ERROR'}, "Invalid scene selected")
            return {'CANCELLED'}

        my_vars = context.scene.tmy_variables
        their_vars = bpy.data.scenes[self.scene].tmy_variables

        for name, variable in their_vars.items():
            target = my_vars[name] if name in my_vars else my_vars.add()
            for k, v in variable.items():
                target[k] = v

        return {'FINISHED'}


REGISTER_CLASSES = [AddVariable, RemoveVariable, ImportVariablesFromScene]
