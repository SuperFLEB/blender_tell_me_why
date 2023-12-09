from types import ModuleType
from typing import Callable, Type
import bpy
from . import util

if "_LOADED" in locals():
    import importlib

    for mod in (util,):  # list all imports here
        importlib.reload(mod)
_LOADED = True

"""
This library contains helper functions useful in setup and management of Blender addons.
It is required by the __init__.py, so don't remove it unless you fix dependencies.
"""


def menuitem(cls: bpy.types.Operator | bpy.types.Menu, operator_context: str = "EXEC_DEFAULT") -> Callable:
    if issubclass(cls, bpy.types.Operator):
        def operator_fn(self, context):
            self.layout.operator_context = operator_context
            if (not hasattr(cls, "can_show")) or cls.can_show(context):
                self.layout.operator(cls.bl_idname)

        return operator_fn
    if issubclass(cls, bpy.types.Menu):
        def submenu_fn(self, context):
            self.layout.menu(cls.bl_idname)

        return submenu_fn
    raise Exception(f"Tell Me Why: Unknown menu type for menu {cls}. The developer screwed up.")


def warn_unregisterable(registerable_modules: list[ModuleType]) -> None:
    def can_register(module: ModuleType) -> bool:
        return hasattr(module, "REGISTER_CLASSES") or hasattr(module, "REGISTER_FUNCTIONS") or hasattr(module, "UNREGISTER_FUNCTIONS")


def get_registerable_classes(registerable_modules: list[ModuleType]) -> list[Type]:
    module_classes = [m.REGISTER_CLASSES for m in registerable_modules if hasattr(m, "REGISTER_CLASSES")]
    if len(module_classes) < len(registerable_modules):
        print("(!) Some modules did not contain valid REGISTER_CLASSES arrays: ",
              [m.__name__ for m in registerable_modules if not hasattr(m, "REGISTER_CLASSES")])
    flat_classes = [c for mc in module_classes for c in mc]
    # Deduplicate and preserve order using the Python 3.7+ fact that dicts keep insertion order
    dedupe_classes = list(dict.fromkeys(flat_classes))
    return dedupe_classes


def register_menus(menus: list[tuple[str, Callable]]):
    for m in menus:
        getattr(bpy.types, m[0]).append(m[1])


def unregister_menus(menus: list[tuple[str, Callable]]):
    for m in menus[::-1]:
        getattr(bpy.types, m[0]).remove(m[1])


def multiline_label(context, layout: bpy.types.UILayout = None, text: str = None, icon: str = None,
                    omit_empty: bool = False, width: int = None) -> None:
    if omit_empty and not text:
        return
    blank_icon = {"icon": "BLANK1"} if icon else {}
    icon = {"icon": icon} if icon else {}

    container = layout.column()
    container.scale_y = 0.8

    lines = util.wordwrap(text, width or (context.region.width / 8))
    container.label(text=lines[0], **icon)
    for line in lines[1:]:
        lbl = container.label(text=line, **blank_icon)
