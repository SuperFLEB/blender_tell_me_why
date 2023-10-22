import collections.abc
import re
from math import isclose
from typing import Callable


def flatten(list_of_lists: list[list[any]]) -> list[any]:
    """Flatten a list of lists"""
    return [item for sublist in list_of_lists for item in sublist]


def wordwrap(string: str, length: int) -> list[str]:
    """Word wrap a string to the given length"""
    words = [word for word in re.split(" +", string) if word]
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


def uilist_sort(items: list[any], make_sortable_fn: Callable[[any], any] = lambda value: value) -> list[int]:
    """Given an unsorted list and a normalizing function, generates a list of movement directives in the form that
    UIList sorting requires."""

    # Return a list (of the same length) with the values being what index the value at that index should be moved to.
    # So, if what is index 4 should be at index 2, the array should have 2 at its index 4

    moves = [0] * len(items)

    # Achieve this by enumerating the original list, sorting the enumeration by value, then enumerating that, so
    # we have both the original position and the new (desired) one...
    for (new_index, (original_index, _)) in enumerate(
            sorted(enumerate(items), key=lambda item: make_sortable_fn(item[1]))):
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

    if hasattr(value, "__len__") and len(value) > 1:
        return "(" + ", ".join([format_prop_value(v) for v in value]) + ")"

    return numstr(value)


def compare(a, b, float_precision: float = 0.00001):
    """Returns true if a and b's elements are all equal, to within float_precision"""
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


def is_iterable(thing: any):
    return (isinstance(thing, collections.abc.Iterable) or hasattr(thing, "__getitem__")) and not isinstance(thing, str)
