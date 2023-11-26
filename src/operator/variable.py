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
        count = len(variable_lib.get_scene_variables())
        if index >= count:
            tmy.variable_selected_index = count - 1
        return {'FINISHED'}


class AddGlobalLibVariable(Operator):
    """Add a variable to the global library"""
    bl_idname = "tell_me_why.add_global_lib_variable"
    bl_label = "Add Variable"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context) -> Set[str]:
        prefs = bpy.context.preferences.addons[package_name].preferences
        tmy = context.window_manager.tell_me_why_globals
        tmy.variable_selected_index_prefs = variable_lib.add(prefs.global_variables_library)
        return {'FINISHED'}


class RemoveGlobalLibVariable(Operator):
    """Remove a variable from the global library"""
    bl_idname = "tell_me_why.remove_global_lib_variable"
    bl_label = "Remove Variable"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context) -> Set[str]:
        prefs = bpy.context.preferences.addons[package_name].preferences
        tmy = context.window_manager.tell_me_why_globals
        variable_lib.remove(tmy.variable_selected_index_prefs, prefs.global_variables_library)
        tmy.variable_selected_index_prefs = -1
        return {'FINISHED'}


class ImportVariablesOperator(Operator):

    @classmethod
    def import_variables(cls, source, destination):
        for name, variable in source.items():
            target = destination[name] if name in destination else destination.add()
            for k, v in variable.items():
                target[k] = v


class ImportVariablesFromScene(ImportVariablesOperator):
    """Import variables from the scene, overwriting current values if they exist"""
    bl_idname = "tell_me_why.import_variable_from_scene"
    bl_label = "(Invalid Scene)"
    bl_options = {'REGISTER', 'UNDO'}

    scene: bpy.props.StringProperty()

    def execute(self, context):
        if not self.scene or not self.scene in bpy.data.scenes or context.scene.name == self.scene:
            self.report({'ERROR'}, "Invalid scene selected")
            return {'CANCELLED'}
        self.import_variables(bpy.data.scenes[self.scene].tmy_variables, context.scene.tmy_variables)
        return {'FINISHED'}

class ImportVariablesFromGlobalLib(ImportVariablesOperator):
    """Import variables from the global library, overwriting current values if they exist"""
    bl_idname = "tell_me_why.import_variable_from_global_library"
    bl_label = "Variable Library (Preferences)"
    bl_options = {'REGISTER', 'UNDO'}

    scene: bpy.props.StringProperty()

    def execute(self, context):
        prefs = bpy.context.preferences.addons[package_name].preferences
        self.import_variables(prefs.global_variables_library, context.scene.tmy_variables)
        return {'FINISHED'}


REGISTER_CLASSES = [AddVariable, RemoveVariable, AddGlobalLibVariable, RemoveGlobalLibVariable, ImportVariablesFromScene, ImportVariablesFromGlobalLib]
