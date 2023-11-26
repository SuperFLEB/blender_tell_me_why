import bpy
from bpy.types import UIList
from ..lib import formula as formula_lib

if "_LOADED" in locals():
    import importlib

    for mod in (formula_lib, ):  # list all imports here
        importlib.reload(mod)
_LOADED = True

class TMY_UL_Variables(UIList):
    bl_idname = "TMY_UL_Variables"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        split = layout.row()
        evaled_ok = True
        try:
            formula_lib.eval_variable(item.name, item.formula)
        except formula_lib.FormulaExecutionException:
            evaled_ok = False

        split.label(text="", icon='ERROR' if not evaled_ok else 'CHECKMARK')
        split.label(text=item.name)
        split.label(text=item.formula)


REGISTER_CLASSES = [TMY_UL_Variables]
