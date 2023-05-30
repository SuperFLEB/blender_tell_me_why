import bpy
from math import isclose
from collections.abc import Iterable
from . import pkginfo
from . import trust as trust_lib

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, trust_lib):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()

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


class UntrustedExecException(Exception):
    """An exec cannot be attempted because the user has not expressed trust of the current file."""
    pass


class TrustProblemException(Exception):
    """There was a problem determining whether the user trusts the current action."""
    pass


def exec_formula(formula: str, node: bpy.types.NodeInternal):
    if not trust_lib.is_trustable_node(node):
        raise TrustProblemException("Formula was on a node type or location that is not yet supported")

    if _formula_cache.get(formula, None):
        return _formula_cache[formula]
    else:
        try:
            # TODO: Add check for
            result = eval(formula)
            _formula_cache[formula] = result
        except BaseException as e:
            print(f"Failed formula: {e}")
            raise FormulaExecutionException("Your formula is bad and you should feel bad")


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
