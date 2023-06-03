from typing import Iterable, Callable
from math import isclose
import bpy
import re


def flatten(list_of_lists: list[list[any]]) -> list[any]:
    """Flatten a list of lists"""
    return [item for sublist in list_of_lists for item in sublist]


def wordwrap(string: str, length: int) -> list[str]:
    """Word wrap a string to the given length"""
    words = [word for word in re.split(' +', string) if word]
    if not words: return [""]
    lines = [f"{words[0]} "]
    if len(words) > 1:
        for word in words[1:]:
            if len(lines[-1]) + len(word) > length:
                lines.append(f"{word} ")
                continue
            lines[-1] += f"{word} "
    lines = [line[:-1] for line in lines]
    return lines


def get_collection_of_object(obj: bpy.types.Object, default_to_context: bool = True) -> bpy.types.Collection | None:
    """Get the enclosing collection of an Object (caveat: if the object is not in the active scene, this may break)"""

    # If there's only one, return that...
    candidates = [c for c in obj.users_collection]

    if len(candidates) == 0:
        return bpy.context.scene.collection if default_to_context else None

    if len(candidates) == 1:
        return candidates[0]

    # If there are more than one, but one isn't in the current Scene
    # (e.g., it's a RigidBodyWorld), return the first that isn't...
    scene_collections = [bpy.context.scene.collection] + list(bpy.context.scene.collection.children_recursive)
    candidates = [c for c in candidates if c in scene_collections]
    if len(candidates) > 0:
        return candidates[0]

    # Return the first collection from anywhere
    return obj.users_collection[0]


def get_operator_defaults(operator_instance) -> dict[str, any]:
    """Scan annotations on the given instance and all parent classes to find default operator values"""
    defaults = {}
    for cls in [type(operator_instance)] + list(type(operator_instance).__mro__):
        for note_name, note in getattr(cls, '__annotations__', {}).items():
            if hasattr(note, "keywords") and "default" in note.keywords:
                defaults[note_name] = note.keywords["default"]
    return defaults


def reset_operator_defaults(operator_instance, keys: Iterable[str]) -> None:
    """Reset some of an operator's properties to their defaults"""
    defaults = get_operator_defaults(operator_instance)
    for key in keys:
        if key in defaults:
            setattr(operator_instance, key, defaults[key])


def uilist_sort(items: list[any], make_sortable_fn: Callable[[any], any] = lambda value: value) -> list[int]:
    """Given an unsorted list and a normalizing function, generates a list of movement directives in the form that
    UIList sorting requires."""

    # Return a list (of the same length) with the values being what index the value at that index should be moved to.
    # So, if what is index 4 should be at index 2, the array should have 2 at its index 4

    moves = [0] * len(items)

    # Achieve this by enumerating the original list, sorting the enumeration by value, then enumerating that, so
    # we have both the original position and the new (desired) one...
    for (new_index, (original_index, _)) in enumerate(sorted(enumerate(items), key=lambda item: make_sortable_fn(item[1]))):
        # ...then assigning value new_index to list item original_index
        moves[original_index] = new_index

    return moves


def format_prop_value(value, float_decimals: int = 3):
    def numstr(num: int | float) -> str:
        if type(num) is int:
            return str(num)
        if type(num) is float:
            return str(round(num, float_decimals))
        return str(num)

    if type(value) is str:
        return value

    if hasattr(value, '__len__') and len(value) > 1:
        return ("(" + ", ".join([format_prop_value(v) for v in value]) + ")")

    return numstr(value)


def edit_mode_prop(edit_mode: bool, parent: bpy.types.UILayout, data: bpy.types.AnyType, property: str, label: str, label_options: dict = None, prop_options: dict = None, label_text_parser: Callable[[any], str] = lambda val: str(val), dict_object: bool = False):
    if edit_mode:
        value = label_text_parser(data.get(property) if dict_object else data.getattr(property))
        prop_label_layout = parent.row()
        prop_label_layout.label(text=label)
        prop_label_layout.label(text=value, **(label_options if label_options else {}))
    return parent.prop(data=data, property=property, **(prop_options if prop_options else {}))


def compare(a, b, float_precision: float = 0.00001):
    if type(a) is str:
        return a == b
    if hasattr(a, "__len__") != hasattr(b, "__len__"):
        return False
    if hasattr(a, "__len__"):
        return compare_vectors(a, b, float_precision)
    return compare_scalars(a, b, float_precision)


def compare_scalars(a, b, float_precision: float = 0.00001):
    if type(a) is float or type(b) is float:
        return isclose(a, b, rel_tol=float_precision)
    return a == b


def compare_vectors(a, b, float_precision: float = 0.00001):
    for ac, bc in zip(a, b):
        numeric_value = type(ac) in [int, float] and type(bc) in [int, float]
        if numeric_value:
            if not isclose(float(ac), float(bc), rel_tol=float_precision):
                return False
        else:
            if ac != bc:
                return False
    return True
