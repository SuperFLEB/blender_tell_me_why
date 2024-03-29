from typing import Callable

import bpy

from .lib import addon, icons as icons_lib
from .operator import explanation, variable as variable_operators
from .panel import preferences as preferences_panel, n_panel, variables as variables_panel, ul_variables
from .props import wm_props, explanation as explanation_props, variable as variable_props
from .header import node_editor

if "_LOADED" in locals():
    import importlib

    for mod in (
            wm_props, addon, explanation, variable_operators, variable_props, n_panel, variables_panel,
            explanation_props, ul_variables, preferences_panel, node_editor):
        importlib.reload(mod)

_LOADED = True

package_name = __package__

bl_info = {
    "name": "Tell Me Why",
    "description": "Create descriptions, hints, and formulas for node input socket values",
    "author": "FLEB (a.k.a. SuperFLEB)",
    "version": (0, 5, 0),
    "blender": (3, 4, 0),
    "location": "Node Editor",
    "warning": "",  # used for warning icon and text in addons panel
    "doc_url": "https://github.com/SuperFLEB/blender_tell_me_why",
    "tracker_url": "https://github.com/SuperFLEB/blender_tell_me_why/issues",
    "support": "COMMUNITY",
    "category": "Node",
}

menus: list[tuple[str, Callable]] = [
    ("TOPBAR_MT_file", addon.menuitem(explanation.ApplyAllFormulas)),
    ("NODE_HT_header", node_editor.annotations_indicator)
]

# Registerable modules have a REGISTER_CLASSES list that lists all registerable classes in the module
registerable_modules = [
    variable_props,
    ul_variables,
    # preferences_panel MUST be registered before n_panel
    preferences_panel,
    wm_props,
    explanation_props,
    explanation,
    variable_operators,
    n_panel,
    variables_panel
]

registerable_handler_modules = []

def register() -> None:
    icons_lib.register_icons()

    for c in addon.get_registerable_classes(registerable_modules):
        # Attempt to clean up if the addon broke during registration.
        try:
            bpy.utils.unregister_class(c)
        except RuntimeError:
            pass

        bpy.utils.register_class(c)
        if hasattr(c, "post_register") and callable(c.post_register):
            c.post_register()

        print(f"{bl_info['name']} registered class:", c)

        # Once we've registered the prefs, we can set the n-panel's "bl_category" before that's registered
        if c is preferences_panel.TMYPrefsPanel:
            n_panel.set_panel_category_from_prefs()

    for c in registerable_handler_modules:
        if hasattr(c, "REGISTER_HANDLERS"):
            for event_type, handlers in c.REGISTER_HANDLERS.items():
                for h in handlers:
                    print(f"{bl_info['name']} registered {event_type} handler", h)
                    getattr(bpy.app.handlers, event_type).append(h)

    for prop_name, prop_def in wm_props.WM_PROPS.items():
        print(f"{bl_info['name']} registered WM property: ", prop_name)
        PropDefClass = prop_def[0]
        setattr(bpy.types.WindowManager, prop_name, PropDefClass(**prop_def[1]))

    addon.register_menus(menus)


def unregister() -> None:
    for prop_name, prop_def in wm_props.WM_PROPS.items():
        delattr(bpy.types.WindowManager, prop_name)

    for c in registerable_handler_modules:
        if hasattr(c, "REGISTER_HANDLERS"):
            for event_type, handlers in c.REGISTER_HANDLERS.items():
                for h in handlers:
                    print(f"{bl_info['name']} unregistered {event_type} handler", h)
                    getattr(bpy.app.handlers, event_type).remove(h)

    addon.unregister_menus(menus)

    for m in menus[::-1]:
        getattr(bpy.types, m[0]).remove(m[1])

    for c in addon.get_registerable_classes(registerable_modules)[::-1]:
        try:
            bpy.utils.unregister_class(c)
            if hasattr(c, "post_unregister") and callable(c.post_unregister):
                c.post_unregister()
            print(f"{bl_info['name']} unregistered class:", c)
        except RuntimeError as e:
            print(f"{bl_info['name']} failed to registered class:", c, e)
            pass

    icons_lib.unregister_icons()


if __name__ == "__main__":
    register()
