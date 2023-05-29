import bpy
from typing import Set
from bpy.types import Operator, NodeSocket, PropertyGroup
from bpy.props import PointerProperty, StringProperty, BoolProperty, FloatProperty, IntProperty, CollectionProperty
from ..lib import node as node_lib

if "_LOADED" in locals():
    import importlib

    for mod in (node_lib,):  # list all imports here
        importlib.reload(mod)
_LOADED = True


class ExplanationVariable(PropertyGroup):
    name: StringProperty(name="name")
    value: FloatProperty(name="value")
    description: StringProperty(name="description")


bpy.utils.register_class(ExplanationVariable)


class ComponentValueExplanation(PropertyGroup):
    description: StringProperty(name="description", default="")
    use_formula: BoolProperty(name="Use Value/Formula", default=False)
    formula: StringProperty(name="formula", default="")
    # TODO: Make this an ENUM type
    type: StringProperty(name="type", default="float")
    # If the value has been collapsed to a single formula (in the Explanation properties),
    # the formula is expected to return an Iterable of this length. Usually "1" for split components.
    length: IntProperty(name="vector length", min=1, max=4, default=1)
    variables: CollectionProperty(type=ExplanationVariable)


bpy.utils.register_class(ComponentValueExplanation)


class Explanation(PropertyGroup):
    active: BoolProperty(name="active", default=False)
    description: StringProperty(name="Description", default="")
    components: CollectionProperty(type=ComponentValueExplanation)
    split_components: BoolProperty(name="Split components?", default=True)

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
        explanation = socket.explanation
        types = node_lib.get_value_types(socket)
        explanation.active = bool(types)
        for idx, t in enumerate(types):
            val = explanation.components.add()
            val.description = ""
            val.type = t
            val.formula = str(socket.default_value) if len(types) == 1 else str(socket.default_value[idx])
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
