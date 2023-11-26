from typing import Set
from typing import Set

from bpy.props import IntProperty
from bpy.types import Operator

from ..lib import node as node_lib, evaluation as evaluation_lib, formula as formula_lib, util
from ..props import explanation as explanation_props

if "_LOADED" in locals():
    import importlib

    for mod in (node_lib, explanation_props, evaluation_lib, formula_lib, util):  # list all imports here
        importlib.reload(mod)
_LOADED = True


class CreateSocketExplanation(Operator):
    """Add Tell Me Why annotation data for the socket"""
    bl_idname = "tell_me_why.create_explanation"
    bl_label = "Create Tell Me Why Explanation"
    bl_options = {"UNDO"}

    def execute(self, context) -> Set[str]:
        socket = context.operator_socket
        explanation = socket.tmy_explanation

        # Can't detail the value if there's no default value to detail
        if not hasattr(socket, "default_value"):
            explanation.active = True
            return {"FINISHED"}

        types = node_lib.get_value_types(socket)
        explanation.active = bool(types)
        for idx, t in enumerate(types):
            val = explanation.components.add()
            val.description = ""
            val.type = t
            val.formula = ""
        return {"FINISHED"}


class RemoveSocketExplanation(Operator):
    """Remove Tell Me Why annotation data for the socket"""
    bl_idname = "tell_me_why.remove_explanation"
    bl_label = "Remove Tell Me Why Explanation"
    bl_options = {"UNDO"}

    def execute(self, context) -> Set[str]:
        socket = context.operator_socket
        socket.property_unset("tmy_explanation")
        return {"FINISHED"}


def _update_socket(socket, index):
    formula_lib.eval_all_variables()
    evaluated = evaluation_lib.Evaluation(socket)
    return evaluated.apply_result(socket.default_value, index)


class ApplyFormula(Operator):
    """Apply the formula and set the default value of the socket"""
    bl_idname = "tell_me_why.apply_formula"
    bl_label = "Apply Formula"
    bl_options = {"UNDO"}

    component_index: IntProperty(name="component_index", default=0)

    def execute(self, context) -> Set[str]:
        context.operator_socket.default_value = _update_socket(context.operator_socket, self.component_index)
        return {"FINISHED"}


class ApplyAllFormulas(Operator):
    """Apply all Tell Me Why formulas in the file"""
    bl_idname = "tell_me_why.apply_all"
    bl_label = "Apply All Formulas"
    bl_options = {"UNDO"}

    def execute(self, context) -> Set[str]:
        sockets = evaluation_lib.find_formula_sockets()
        successes = 0
        failures = 0
        for socket in sockets:
            for index, component in enumerate(socket.tmy_explanation.components):
                if component.use_formula:
                    try:
                        new_value = _update_socket(socket, index)
                        if not util.compare(new_value, socket.default_value):
                            successes += 1
                            socket.default_value = new_value
                    except:
                        failures += 1

        if failures:
            self.report({"WARNING"}, f"{failures} failed. {successes} values updated.")
        elif successes:
            self.report({"INFO"}, f"{successes} values updated.")
        else:
            self.report({"WARNING"}, "No values updated.")

        return {"FINISHED"}


REGISTER_CLASSES = [CreateSocketExplanation, RemoveSocketExplanation, ApplyFormula, ApplyAllFormulas]
