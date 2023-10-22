from typing import Iterable

import bpy
from bpy.types import NodeSocket

from ..lib import formula as formula_lib, util
from ..props import explanation as explanation_props

if "_LOADED" in locals():
    import importlib

    for mod in (explanation_props, formula_lib, util):  # list all imports here
        importlib.reload(mod)
_LOADED = True


class ValueErrorException(Exception):
    pass


class Evaluation:
    _values: tuple = tuple()
    _results: tuple[float, ...] = tuple()
    _formulas: tuple[str, ...] = tuple()
    _matches: tuple[bool, ...] = tuple()
    _errors: tuple[bool, ...] = tuple()
    _split_components: bool = False

    def __init__(self, socket: NodeSocket):
        explanation = socket.tmy_explanation

        self._values = tuple(socket.default_value) if util.is_iterable(socket.default_value) else (
        socket.default_value,)
        self._split_components = explanation.split_components

        if not self._split_components:
            if not explanation.components[0].use_formula:
                self._results = self._values
                self._formulas = ("",) * len(self._values)
                self._matches = (True,) * len(self._values)
                return

            self._formulas = (explanation.components[0].formula,)
            self._process_results(
                explanation.components[0].formula,
                len(self._values),
                True
            )
            self._process_matches()
            return

        for c_idx, component in enumerate(explanation.components):
            if not component.use_formula:
                self._formulas += (self._values[c_idx],)
                self._results += (self._values[c_idx],)
                self._errors += (False,)
                continue
            self._process_results(
                component.formula,
                expect_len=1,
                extend_to_expected=(not self._split_components)
            )

        self._process_matches()

    def _process_results(self, formula, expect_len: int, extend_to_expected: bool):
        """Evaluate the formula and store the results or the error state"""
        self._formulas += (formula,)

        if formula == "":
            self._results += (0.0,) * expect_len
            self._errors += (True,) * expect_len
            return

        try:
            result = formula_lib.eval_formula(
                formula,
                expect_len=expect_len,
                extend_to_expected=extend_to_expected
            )
            self._results += result
            self._errors += (False,) * expect_len
        except formula_lib.FormulaExecutionException as e:
            self._results += (0.0,) * expect_len
            self._errors += (True,) * expect_len

    def _process_matches(self):
        comparison = [util.compare_scalars(value, self._results[idx]) for idx, value in enumerate(self._values)]
        self._matches = tuple(comparison)

    def get_results(self) -> tuple[float]:
        if self.has_errors():
            raise ValueErrorException("Evaluation failed and results are invalid")
        return self._results

    def is_index_matching(self, index: int, force_split_components: bool = False):
        # If we have a single input (un-split components) we need to compare the whole result,
        # not just the 0th index.

        if index == 0 and not (self._split_components or force_split_components):
            return self.is_matching()

        # If we do have split components, or we've forced the matter, compare only the indexed value
        return self._matches[index]

    def is_matching(self):
        return False not in self._matches

    def is_error(self, index):
        return self._errors[index]

    def has_errors(self):
        return True in self._errors

    def get_formulas(self) -> tuple[str, ...]:
        return self._formulas

    def apply_result(self, current_value: float | Iterable[float], index: int = 0,
                     force_split_components: bool = False) -> float | tuple[float]:
        """Combine the given result index with the given one and return the results, considering split components and
        scalar/list values"""
        results = self.get_results()

        # It's a safe assumption that a single-item result indicates a scalar
        if len(results) == 1:
            return results[0]

        if index != 0 or self._split_components or force_split_components:
            current_value: list[float] = list(current_value)
            current_value[index] = results[index]
            return tuple(current_value)

        return results


def _has_formula(socket: NodeSocket):
    return hasattr(socket, "tmy_explanation") and socket.tmy_explanation.active and any(
        [c for c in socket.tmy_explanation.components if c.use_formula])


def find_formula_sockets():
    """Find all Node Inputs that have active formulas"""
    # Only these locations are scanned for nodes when creating the formula report. Other node types,
    # such as those created in newer versions of Blender, should not be allowed to run,
    # because the user cannot verify them.

    node_locations = {
        "nodes": ["node_groups"],
        "node_tree.nodes": ["materials", "lights", "scenes"],
    }

    sockets = set()

    for loc in node_locations["nodes"]:
        for thing in getattr(bpy.data, loc, []):
            for node in thing.nodes:
                sockets |= {socket for socket in node.inputs if _has_formula(socket)}

    for loc in node_locations["node_tree.nodes"]:
        for thing in getattr(bpy.data, loc, []):
            if hasattr(thing, "node_tree") and hasattr(thing.node_tree, "nodes") and len(thing.node_tree.nodes):
                for node in thing.node_tree.nodes:
                    sockets |= {socket for socket in node.inputs if _has_formula(socket)}

    return sockets
