import bpy
import builtins
import math
from collections.abc import Sequence
from ..vendor.simpleeval import EvalWithCompoundTypes
from . import pkginfo, util

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, util):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()
_formula_cache = {}


class FormulaExecutionException(Exception):
    pass


def formula_accessible_globals() -> dict[str, any]:
    allowed = {
        "names": {
            "eulers": math.e,
            "infinity": math.inf,
            "nan": math.nan,
            "pi": math.pi,
            "tau": math.tau,
        },
        "functions": {},
    }
    # Math methods from the "math" module
    math_methods = ('acos', 'acosh', 'asin', 'asinh', 'atan', 'atan2', 'atanh', 'ceil', 'comb', 'copysign', 'cos',
                    'cosh', 'degrees', 'dist', 'erf', 'erfc', 'exp', 'expm1', 'fabs', 'factorial', 'floor', 'fmod',
                    'frexp', 'fsum', 'gamma', 'gcd', 'hypot', 'inf', 'isclose', 'isfinite', 'isinf', 'isnan', 'isqrt',
                    'lcm', 'ldexp', 'lgamma', 'log', 'log10', 'log1p', 'log2', 'modf', 'nan', 'nextafter', 'perm', 'pi',
                    'pow', 'prod', 'radians', 'remainder', 'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'tau', 'trunc', 'ulp')
    allowed["functions"] |= {(name, getattr(math, name)) for name in math_methods}

    # Math methods from the builtin namespace
    builtin_methods = ('abs', 'divmod', 'max', 'min', 'pow', 'range', 'round', 'sum')
    allowed["functions"] |= {(name, getattr(builtins, name)) for name in builtin_methods}

    return allowed


def _do_eval(formula: str, variables: dict[
    str, int | float | Sequence[float, float, float] | Sequence[float, float, float, float]] = None):

    variables = variables if variables else {}
    allowed = formula_accessible_globals()

    # Any exceptions should be handled in the caller
    evaluator = EvalWithCompoundTypes(functions=allowed["functions"], names=allowed["names"] | variables)
    return evaluator.eval(formula)


def eval_formula(
        formula: str,
        expect_len: int = 1,
        extend_to_expected: bool = False
) -> tuple[float, ...]:
    if _formula_cache.get(formula, None):
        result = _formula_cache[formula]
    else:
        try:
            result = _do_eval(formula)
            _formula_cache[formula] = result
        except BaseException as e:
            raise FormulaExecutionException(f"Formula raised an exception: {e}")

    if type(result) is str or not hasattr(result, "__len__"):
        result = [result]

    result_len = len(result)

    if result_len != expect_len and not extend_to_expected:
        raise FormulaExecutionException("Unexpected result length")

    # Extend the list if the result is shorter
    if result_len < expect_len:
        return tuple(result + (result[-1:] * (expect_len - result_len)))

    # Truncate the list if the result is longer
    if result_len > expect_len:
        return tuple(result[0:expect_len])

    # Return the list if all is well
    return tuple(result)
