from typing import Set

import bpy

from ..lib import variable as variable_lib

if "_LOADED" in locals():
    import importlib

    for mod in (variable_lib,):  # list all imports here
        importlib.reload(mod)
_LOADED = True

if "_LOADED" in locals():
    import importlib

    for mod in []:  # list all imports here
        importlib.reload(mod)
_LOADED = True


class AddVariable(bpy.types.Operator):
    """Add a scene variable"""
    bl_idname = "tell_me_why.add_scene_variable"
    bl_label = "Add Scene Variable"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context) -> Set[str]:
        tmy = context.window_manager.tell_me_why_globals
        tmy.variable_selected_index = variable_lib.add()
        return {'FINISHED'}


class RemoveVariable(bpy.types.Operator):
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


REGISTER_CLASSES = [AddVariable, RemoveVariable]
