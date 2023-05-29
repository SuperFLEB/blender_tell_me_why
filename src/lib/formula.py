import bpy
from math import isclose
from collections.abc import Iterable

################################################
# WARNING! WARNING! WARNING! WARNING! WARNING! #
################################################
#
# These functions use unchecked, unsanitized eval without user interaction.
# DO NOT ACTIVATE THIS PLUGIN AND OPEN UNTRUSTED FILES UNTIL THIS IS MITIGATED!
#
################################################

_formula_cache = {}


class FormulaExecutionException(Exception):
    pass


def does_value_equal_formula_result(value, formula: str, float_precision: float = 0.00001):
    if _formula_cache.get(formula, None):
        result = _formula_cache[formula]
    else:
        try:
            result = eval(formula)
            _formula_cache[formula] = result
        except BaseException as e:
            print(f"Failed formula: {e}")
            raise FormulaExecutionException("Your formula is bad and you should feel bad")

    multi_value = type(value) is not str and isinstance(value, Iterable)
    multi_result = type(result) is not str and isinstance(result, Iterable)
    numeric_value = type(value) in [int, float]

    if multi_value and not multi_result:
        result = [result for sub in value]
        multi_result = True

    if not multi_value and multi_result:
        if numeric_value:
            result = sum(result) / len(result)
            multi_result = False
        else:
            return False

    if not multi_value:
        value = [value]
        result = [result]

    for v, r in zip(value, result):
        if numeric_value:
            if not isclose(float(v), float(r), rel_tol=float_precision):
                return False
        else:
            if v != r:
                return False
    return True
