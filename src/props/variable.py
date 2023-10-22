import bpy
from bpy.types import PropertyGroup, Scene, AnyType
from bpy.props import StringProperty, CollectionProperty, IntProperty

class TMYVariable(PropertyGroup):
    """Variable definition"""

    name: StringProperty(
        name="Name",
        description="The name of the variable",
        default="var"
    )

    formula: StringProperty(
        name="Formula",
        description="Value or formula for the variable",
        default="0"
    )

    @classmethod
    def post_register(cls):
        Scene.tmy_variables = CollectionProperty(type = cls)
        Scene.tmy_variable_pointer = IntProperty()

REGISTER_CLASSES = [ TMYVariable ]