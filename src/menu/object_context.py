from ..operator import explanation
from ..operator import an_operator
from ..operator import an_operator_with_a_uilist
from ..lib import addon

if "_LOADED" in locals():
    import importlib

    for mod in (explanation, an_operator, an_operator_with_a_uilist,):  # list all imports here
        importlib.reload(mod)
_LOADED = True


class TellMeWhySubmenu(addon.SimpleMenu):
    bl_idname = 'tell_me_why_MT_tell_me_why_submenu'
    bl_label = 'Tell Me Why'
    items = [
        (explanation.CreateExplanation, "EXEC_DEFAULT"),
        an_operator.AnOperator,
        an_operator_with_a_uilist.AnOperatorWithUIList
    ]
    operator_context = "INVOKE_DEFAULT"


REGISTER_CLASSES = [TellMeWhySubmenu]
