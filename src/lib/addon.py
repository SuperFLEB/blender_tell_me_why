import bpy
import glob
from pathlib import Path
from bpy.types import Operator, Menu
from typing import Callable, Type
from types import ModuleType
from . import util

from hashlib import md5

"""
This library contains helper functions useful in setup and management of Blender addons.
It is required by the __init__.py, so don't remove it unless you fix dependencies.
"""

_icons = {}
icons = {}
_builtin_icons = {ei.name: ei.value for ei in bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items}


class SimpleMenu(Menu):
    # If the menu item needs its own operator context, use a tuple of (OperatorClass, "context")
    items: list[Operator | Menu | str | None | tuple[Operator, str]] = []
    operator_context: str = "INVOKE_REGION_WIN"

    def draw(self, context) -> None:
        self.layout.operator_context = self.operator_context

        for item in self.items:
            layout = self.layout
            layout.operator_context = self.operator_context

            if item is None:
                layout.separator()
                continue
            if type(item) is str:
                layout.label(text=item)
                continue

            if type(item) is tuple:
                if len(item) == 2 and issubclass(item[0], Operator) and type(item[1]) is str:
                    layout = layout.column()
                    layout.operator_context = item[1]
                    item = item[0]
                else:
                    print("(!) Bad tuple in SimpleMenu: ", item)

            if (not hasattr(item, 'can_show')) or item.can_show(context):
                if issubclass(item, bpy.types.Menu):
                    layout.menu(item.bl_idname)
                    continue
                if issubclass(item, bpy.types.Operator):
                    layout.operator(item.bl_idname)
                    continue

            print("(!) Unknown menu item type in SimpleMenu: ", item)


def menuitem(cls: bpy.types.Operator | bpy.types.Menu, operator_context: str = "EXEC_DEFAULT") -> Callable:
    if issubclass(cls, bpy.types.Operator):
        def operator_fn(self, context):
            self.layout.operator_context = operator_context
            if (not hasattr(cls, 'can_show')) or cls.can_show(context):
                self.layout.operator(cls.bl_idname)
        return operator_fn
    if issubclass(cls, bpy.types.Menu):
        def submenu_fn(self, context):
            self.layout.menu(cls.bl_idname)

        return submenu_fn
    raise Exception(f"Tell Me Why: Unknown menu type for menu {cls}. The developer screwed up.")


def get_registerable_classes(registerable_modules: list[ModuleType]) -> list[Type]:
    module_classes = [m.REGISTER_CLASSES for m in registerable_modules if hasattr(m, "REGISTER_CLASSES")]
    if len(module_classes) < len(registerable_modules):
        print("(!) Some modules did not contain valid REGISTER_CLASSES arrays: ", [m.__name__ for m in registerable_modules if not hasattr(m, 'REGISTER_CLASSES')])
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


def multiline_label(context, layout: bpy.types.UILayout = None, text: str = None, icon: str = None, omit_empty: bool = False) -> None:
        if omit_empty and not text:
            return
        blank_icon = {"icon": "BLANK1"} if icon else {}
        icon = {"icon": icon} if icon else {}

        container = layout.column()
        container.scale_y = 0.8
        lines = util.wordwrap(text, context.region.width / 10)
        container.label(text=lines[0], **icon)
        for line in lines[1:]:
            lbl = container.label(text=line, **blank_icon)


def register_icons():
    global _icons, icons
    _icons = bpy.utils.previews.new()
    icon_files = Path(__file__).parents[1].joinpath('icons').glob('*.png')
    for icon_file in icon_files:
        stem = icon_file.stem
        new_icon = _icons.load(stem, str(icon_file), 'IMAGE')
        icons[stem] = new_icon.icon_id
        print(f"Registering icon: {stem} (ID {icons[stem]} as {icon_file}")


def unregister_icons():
    global _icons, icons
    bpy.utils.previews.remove(_icons)


def icon_value(name: str) -> int:
    """Return an icon_value for a given icon_name, either from the builtin icons set or from the registered custom icons.
    Returns NONE (0) if an invalid icon name is given."""
    global _builtin_icons
    id = _builtin_icons.get(name)
    if id:
        return id
    custom = _icons.get(name)
    if custom:
        return custom.icon_id
    return 0
