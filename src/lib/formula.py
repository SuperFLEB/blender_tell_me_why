import bpy
from collections.abc import Iterable, Sequence, Callable
import builtins
import re
import math
from . import pkginfo
from . import trust as trust_lib
from . import util

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, trust_lib, util):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()
_formula_cache = {}


class FormulaExecutionException(Exception):
    pass


class FormulaSafetyException(FormulaExecutionException):
    pass


class TrustProblemException(Exception):
    """There was a problem determining whether the user trusts the current action."""
    pass


class UntrustedEvalException(TrustProblemException):
    """An eval cannot be attempted because the user has not expressed trust of the current file."""
    pass


def is_suspicious_var_name(name: str) -> bool:
    if "__" in name:
        return True

    if name in builtins.__dict__.keys():
        return True

    # This should handle most other attempts at injection, like semicolons, spaces, newlines, that sort of thing
    only_alphanumeric_and_underscore_starting_with_alpha = re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')
    if not only_alphanumeric_and_underscore_starting_with_alpha.match(name):
        return True

    # Not necessarily suspicious but not allowed since it masks formula-accessible globals
    if name in formula_accessible_globals().keys():
        return True

    return False


def is_suspicious_var_value(value: any) -> bool:
    if type(value) not in [list, tuple]:
        value = (value,)
    for v in value:
        if type(v) not in [int, float]:
            return True
    return False


def is_suspicious_formula(formula: str) -> bool:
    for bad_chars in ["__", "'", '"', "\n", "\t", "\r", ";"]:
        if bad_chars in formula:
            return True
    attribute_access = re.compile('\\.[^0-9]')
    if attribute_access.match(formula):
        return True
    non_numeric_subscript = re.compile('\\[[^0-9 ]+]')
    if non_numeric_subscript.match(formula):
        return True
    return False


def formula_accessible_globals() -> dict[str, any]:
    global_scope = {}

    # Math methods from the "math" module
    math_methods = ('acos', 'acosh', 'asin', 'asinh', 'atan', 'atan2', 'atanh', 'ceil', 'comb', 'copysign', 'cos',
                    'cosh', 'degrees', 'dist', 'erf', 'erfc', 'exp', 'expm1', 'fabs', 'factorial', 'floor', 'fmod',
                    'frexp', 'fsum', 'gamma', 'gcd', 'hypot', 'inf', 'isclose', 'isfinite', 'isinf', 'isnan', 'isqrt',
                    'lcm', 'ldexp', 'lgamma', 'log', 'log10', 'log1p', 'log2', 'modf', 'nan', 'nextafter', 'perm', 'pi',
                    'pow', 'prod', 'radians', 'remainder', 'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'tau', 'trunc', 'ulp')
    global_scope |= {(name, getattr(math, name)) for name in math_methods}

    # Add this under a different name so people can use "e" as a normal variable
    global_scope['eulers_number'] = math.e

    # Math methods from the builtin namespace
    builtin_methods = ('abs', 'divmod', 'max', 'min', 'pow', 'range', 'round', 'sum')
    global_scope |= {(name, getattr(builtins, name)) for name in builtin_methods}

    return global_scope


def paranoid_eval(formula: str, variables: dict[str, int | float | Sequence[float, float, float] | Sequence[float, float, float, float]] = None):
    if not trust_lib.are_formulas_enabled():
        raise FormulaSafetyException("Formula evaluation has been disabled")

    variables = variables if variables else {}
    for k, v in variables.items():
        if is_suspicious_var_name(k):
            raise FormulaSafetyException(f"Variable name {k} is suspicious or not allowed")
        if is_suspicious_var_value(v):
            raise FormulaSafetyException(f"Variable {k} value is suspicious: {v}")
    if is_suspicious_formula(formula):
        raise FormulaSafetyException(f"Formula is suspicious: {formula}")

    allowed = formula_accessible_globals() | variables
    allowed_names = allowed.keys()

    # Precompile the statement and check names
    compiled_formula = compile(formula, "<TMY Formula>", "eval")
    names = compiled_formula.co_names
    for n in names:
        if n not in allowed_names:
            raise FormulaSafetyException(f"Name is not allowed: {n}")

    return eval(compiled_formula, {"__builtins__": allowed}, {})


def eval_formula(formula: str, node: bpy.types.NodeInternal, expect_len: int = 1, extend_to_expected: bool = False):
    if not trust_lib.is_trustable_node(node):
        raise TrustProblemException("Formula was on a node type or location that is not yet supported")

    if not trust_lib.is_file_trusted():
        raise UntrustedEvalException("User has not granted trust for this file")

    if _formula_cache.get(formula, None):
        result = _formula_cache[formula]
    else:
        try:
            result = paranoid_eval(formula)
            _formula_cache[formula] = result
        except FormulaSafetyException as e:
            print(e)
            raise e
        except BaseException as e:
            raise FormulaExecutionException(f"Formula raised an exception: {e}")

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

