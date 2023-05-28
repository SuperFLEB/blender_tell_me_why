import bpy
from typing import Set
from bpy.types import Operator, NodeSocket, PropertyGroup
from bpy.props import StringProperty, BoolProperty

if "_LOADED" in locals():
    import importlib

    for mod in ():  # list all imports here
        importlib.reload(mod)
_LOADED = True


class Explanation(PropertyGroup):
    active: BoolProperty(name="active", default=False)
    description: StringProperty(name="description", default="")
    formula: StringProperty(name="formula", default="")

    @classmethod
    def post_register(cls):
        NodeSocket.explanation = bpy.props.PointerProperty(type=cls, name="explanation")


class CreateSocketExplanation(Operator):
    """Initialize Tell Me Why data for a given node"""
    bl_idname = "tell_me_why.create_explanation"
    bl_label = "Create Tell Me Why Explanation"
    bl_options = {'UNDO'}

    def execute(self, context) -> Set[str]:
        socket = context.operator_socket
        socket.explanation.active = True
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


REGISTER_CLASSES = [Explanation, CreateSocketExplanation, RemoveSocketExplanation]
