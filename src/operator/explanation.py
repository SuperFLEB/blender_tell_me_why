import bpy
from typing import Set
from bpy.types import Operator, NodeSocket, PropertyGroup
from bpy.props import PointerProperty, StringProperty, BoolProperty, FloatProperty, IntProperty, CollectionProperty
from ..lib import node as node_lib, explanation as explanation_lib, util
from ..props import explanation as explanation_props

if "_LOADED" in locals():
    import importlib

    for mod in (node_lib, explanation_props, explanation_lib, util):  # list all imports here
        importlib.reload(mod)
_LOADED = True


class CreateSocketExplanation(Operator):
    """Initialize Tell Me Why data for a given node"""
    bl_idname = "tell_me_why.create_explanation"
    bl_label = "Create Tell Me Why Explanation"
    bl_options = {'UNDO'}

    def execute(self, context) -> Set[str]:
        socket = context.operator_socket
        explanation = socket.explanation

        # Can't detail the value if there's no default value to detail
        if not hasattr(socket, 'default_value'):
            explanation.active = True
            return {'FINISHED'}

        types = node_lib.get_value_types(socket)
        explanation.active = bool(types)
        for idx, t in enumerate(types):
            val = explanation.components.add()
            val.description = ""
            val.type = t
            val.formula = ""
        return {'FINISHED'}


class RemoveSocketExplanation(Operator):
    """Initialize Tell Me Why data for a given node"""
    bl_idname = "tell_me_why.remove_explanation"
    bl_label = "Remove Tell Me Why Explanation"
    bl_options = {'UNDO'}

    def execute(self, context) -> Set[str]:
        socket = context.operator_socket
        socket.property_unset('explanation')
        return {'FINISHED'}


def _update_socket(socket, index):
    evaluated = explanation_lib.Evaluation(socket)
    return evaluated.apply_result(socket.default_value, index)


class ApplyFormula(Operator):
    """Initialize Tell Me Why data for a given node"""
    bl_idname = "tell_me_why.apply_formula"
    bl_label = "Apply Formula"
    bl_options = {'UNDO'}

    component_index: IntProperty(name="component_index", default=0)

    def execute(self, context) -> Set[str]:
        context.operator_socket.default_value = _update_socket(context.operator_socket, self.component_index)
        return {'FINISHED'}


class ApplyAllFormulas(Operator):
    """Apply all formulas in the file"""
    bl_idname = "tell_me_why.apply_all"
    bl_label = "Apply All Formulas"
    bl_options = {'UNDO'}

    def execute(self, context) -> Set[str]:
        sockets = explanation_lib.find_formula_sockets()
        count = 0
        for socket in sockets:
            for index, component in enumerate(socket.explanation.components):
                if component.use_formula:
                    new_value = _update_socket(socket, index)
                    if not util.compare(new_value, socket.default_value):
                        count += 1
                        socket.default_value = new_value
        if count:
            self.report({"INFO"}, f"{count} formulas updated")
        else:
            self.report({"INFO"}, "No formulas updated")

        return {'FINISHED'}


REGISTER_CLASSES = [CreateSocketExplanation, RemoveSocketExplanation, ApplyFormula, ApplyAllFormulas]
