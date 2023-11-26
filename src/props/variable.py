import re

from bpy.props import StringProperty, CollectionProperty
from bpy.types import PropertyGroup, Scene


def set_valid_name(self, value):
    valid_name = re.sub(r"[^A-Za-z0-9]", "_", value)
    valid_name = re.sub(r"^([0-9])", r"_\1", valid_name)
    self["name"] = valid_name


def get_name(self):
    return self["name"]


class TMYVariable(PropertyGroup):
    """Variable definition"""

    name: StringProperty(
        name="Name",
        description="The name of the variable",
        default="var",
        set=set_valid_name,
        get=get_name
    )

    formula: StringProperty(
        name="Formula",
        description="Value or formula for the variable",
        default="0"
    )

    @classmethod
    def post_register(cls):
        Scene.tmy_variables = CollectionProperty(type=cls)

    @classmethod
    def post_unregister(cls):
        del Scene.tmy_variables


REGISTER_CLASSES = [TMYVariable]
