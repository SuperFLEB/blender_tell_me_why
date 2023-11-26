import builtins
import math
from collections.abc import Sequence

from . import pkginfo, util, variable as variable_lib
from ..vendor.simpleeval import EvalWithCompoundTypes

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, util, variable_lib):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()

# formula text: formula result
_formula_cache: dict[str, str] = {}
# name: formula text
_variable_formula_cache: dict[str, str] = {}
# formula text: formula result
_variable_eval_cache: dict[str, tuple[float, ...]] = {}


class FormulaExecutionException(Exception):
    pass


def default_allowed() -> dict[str, any]:
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
    math_methods = ("acos", "acosh", "asin", "asinh", "atan", "atan2", "atanh", "ceil", "comb", "copysign", "cos",
                    "cosh", "degrees", "dist", "erf", "erfc", "exp", "expm1", "fabs", "factorial", "floor", "fmod",
                    "frexp", "fsum", "gamma", "gcd", "hypot", "inf", "isclose", "isfinite", "isinf", "isnan", "isqrt",
                    "lcm", "ldexp", "lgamma", "log", "log10", "log1p", "log2", "modf", "nan", "nextafter", "perm", "pi",
                    "pow", "prod", "radians", "remainder", "sin", "sinh", "sqrt", "tan", "tanh", "tau", "trunc", "ulp")
    allowed["functions"] |= {(name, getattr(math, name)) for name in math_methods}

    # Math methods from the builtin namespace
    builtin_methods = ("abs", "divmod", "max", "min", "pow", "range", "round", "sum")
    allowed["functions"] |= {(name, getattr(builtins, name)) for name in builtin_methods}

    return allowed


def _do_eval(formula: str, variables: dict[str, int | float | Sequence[float, ...]] = None):
    variables = variables if variables else {}
    allowed = default_allowed()
    try:
        evaluator = EvalWithCompoundTypes(functions=allowed["functions"], names=allowed["names"] | variables)
        return evaluator.eval(formula)
    except BaseException as e:
        raise FormulaExecutionException(f"Formula raised an exception: {e}")


def eval_formula(
        formula: str,
        expect_len: int = None,
        extend_to_expected: bool = False,
        wrap_singles: bool = False
) -> tuple[float, ...]:
    global _formula_cache

    # eval_all_variables MUST come before any _formula_cache reads,
    # as part of its job is invalidating the formula cache if variables change
    variables = eval_all_variables()

    if (result := _formula_cache.get(formula, None)) is None:
        result = _do_eval(formula, variables)
        _formula_cache[formula] = result

    if type(result) is str or not hasattr(result, "__len__"):
        result = [result]

    result_len = len(result)

    if expect_len is not None:
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


def eval_variable(name: str, formula: str):
    # Since variables can't use other variables, there's always a 1:1 relationship between formula and value, so we can
    # associate formula with value in a cache
    global _variable_formula_cache, _variable_eval_cache, _formula_cache
    if _variable_formula_cache.get(name, None) == formula:
        value = _variable_eval_cache.get(formula, None)
        if value is not None:
            return value

    # If variables have changed, the formula_cache is invalid
    if _formula_cache:
        _formula_cache = {}

    result = _do_eval(formula, {})
    try:
        result = tuple([float(r) for r in result]) if util.is_iterable(result) else float(result)
    except BaseException as e:
        raise FormulaExecutionException(f"Variable evaluation of \"{name}\" raised an exception: {e}")

    _variable_formula_cache[name] = formula
    _variable_eval_cache[formula] = result
    return result


def reset_variable_cache():
    """Reset variable name-to-value and formula caches, e.g., after deleting a variable
    and possibly invalidating formulas"""
    global _variable_formula_cache, _formula_cache
    _variable_formula_cache = variable_lib.get_formulas()
    _formula_cache = {}


def eval_all_variables() -> dict[str, int | float | tuple[float, ...]]:
    evaled_vars = {}
    for v in variable_lib.get_scene_variables():
        try:
            evaled_vars[v.name] = eval_variable(v.name, v.formula)
        except FormulaExecutionException as e:
            print(f"Error processing variable \"{v.name}\": {e}")
    return evaled_vars
