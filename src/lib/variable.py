import re

import bpy
from bpy.types import AnyType

from ..lib import formula as formula_lib
from ..props import variable as variable_prop

_VAR_PREFIX = "var"

if "_LOADED" in locals():
    import importlib

    for mod in (variable_prop, formula_lib,):  # list all imports here
        importlib.reload(mod)
_LOADED = True


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
    name = _VAR_PREFIX if last_existing is None else f"{_VAR_PREFIX}{last_existing + 1}"
    parent.add()
    parent[-1].name = name
    return len(parent) - 1


def remove(index: int) -> None:
    """Remove a variable from the scene by collection index"""
    parent = bpy.context.scene.tmy_variables
    parent.remove(index)
    formula_lib.reset_variable_cache()


def remove_by_name(name: str) -> bool:
    """Remove a variable from the scene by index"""
    variables = get_variables()
    for idx, variable in enumerate(variables):
        if variable.name == name:
            remove(idx)
            return True
    return False


def get_variables() -> list[variable_prop.TMYVariable]:
    """Get TMYVariable objects for all variables"""
    parent = bpy.context.scene.tmy_variables
    return list(parent)


def get_variables_pointer() -> tuple[AnyType, str]:
    """Get the object/key pointer to where variables are stored (for UILists, etc)"""
    return bpy.context.scene, "tmy_variables"


def get_formulas() -> dict[str, str]:
    """Get a dict of name:formula for variables"""
    return {v.name: v.formula for v in get_variables()}
