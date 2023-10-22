import bpy
import re
from bpy.types import PropertyGroup, Scene, AnyType
from bpy.props import StringProperty, CollectionProperty, IntProperty

_VAR_PREFIX = "var"

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

def add() -> int:
    """Add a variable to the scene"""
    parent = bpy.context.scene.tmy_variables
    match_generic_name = re.compile(f'{_VAR_PREFIX}(\d+)$')
    last_existing = None
    for variable in parent:
        if variable.name == _VAR_PREFIX:
            last_existing = 0
            continue
        if match := match_generic_name.match(variable.name):
            last_existing = int(match[1])
    name = _VAR_PREFIX if last_existing is None else f"{_VAR_PREFIX}{last_existing+1}"
    parent.add()
    parent[-1].name = name
    return len(parent) - 1


def remove(index: int) -> None:
    """Remove a variable from the scene by collection index"""
    parent = bpy.context.scene.tmy_variables
    parent.remove(index)


def remove_by_name(name: str) -> bool:
    """Remove a variable from the scene by index"""
    variables = get_variables()
    for idx, variable in enumerate(variables):
        if variable.name == name:
            remove(idx)
            return True
    return False


def get_variables() -> list[TMYVariable]:
    parent = bpy.context.scene.tmy_variables
    return list(parent)

def get_variables_pointer() -> tuple[AnyType, str]:
    return bpy.context.scene, "tmy_variables"

def get_formulas() -> dict[str, str]:
    return {v.name:v.formula for v in get_variables()}

REGISTER_CLASSES = [ TMYVariable ]