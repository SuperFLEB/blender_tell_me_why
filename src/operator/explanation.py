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


bpy.utils.register_class(ComponentValueExplanation)


def set_split_components(self, value):
    # Collapse existing formulas to a tuple if we are turning off split_components and all are used
    if not (value or [c for c in self.components if not (c and c['use_formula'])]):
        formulas = [c['formula'] for c in self.components]
        for c in self.components[1:]:
            c['formula'] = ""
            c['description'] = ""
            c['use_formula'] = False
        self.components[0]['formula'] = f"({', '.join(formulas)})"
    else:
        for c in self.components:
            c['formula'] = ""
            c['description'] = ""
            c['use_formula'] = False
    self['split_components'] = value


def get_split_components(self):
    return self.get('split_components', False)


class Explanation(PropertyGroup):
    active: BoolProperty(name="active", default=False)
    description: StringProperty(name="Description", default="")
    components: CollectionProperty(type=ComponentValueExplanation)
    variables: CollectionProperty(type=ExplanationVariable)
    split_components: BoolProperty(name="Split components", default=True, set=set_split_components, get=get_split_components)

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
