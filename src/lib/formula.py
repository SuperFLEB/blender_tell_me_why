import bpy
from collections.abc import Iterable
from . import pkginfo
from . import trust as trust_lib
from . import util

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, trust_lib, util):  # list all imports here
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


def exec_formula(formula: str, node: bpy.types.NodeInternal, expect_len: int = 1, extend_to_expected: bool = False):
    if not trust_lib.is_trustable_node(node):
        raise TrustProblemException("Formula was on a node type or location that is not yet supported")

    if _formula_cache.get(formula, None):
        result = _formula_cache[formula]
    else:
        try:
            result = eval(formula)
            _formula_cache[formula] = result
        except BaseException as e:
            raise FormulaExecutionException("Formula caused an error")

    if type(result) is str or not hasattr(result, "__len__"):
        result = [result]

    result_len = len(result)

    if result_len != expect_len and not extend_to_expected:
        raise FormulaExecutionException("Unexpected result length")

    if expect_len == 1:
        # Return a scalar
        return result[0]
    elif result_len < expect_len:
        # Extend the list
        return result + (result[-1:] * (expect_len - result_len))
    elif result_len > expect_len:
        # Truncate the list
        return result[0:expect_len]

    return result

def compare_to_formula(value, formula: str, node: bpy.types.NodeInternal, float_precision: float = 0.00001):
    value_len = len(value) if type(value) is not str and hasattr(value, '__len__') else 1
    result = exec_formula(formula, node, value_len, extend_to_expected=True)

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

    return util.compare_vectors(value, result, float_precision)


