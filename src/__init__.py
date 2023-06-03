from typing import Callable
import bpy
from .lib import addon
from .operator import explanation
from .operator import trust as trust_op
from .panel import preferences as preferences_panel
from .panel import n_panel
from .props import wm_props

if "_LOADED" in locals():
    import importlib

    for mod in (wm_props, addon, explanation, preferences_panel, n_panel, trust_op):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = __package__

bl_info = {
    "name": "Tell Me Why",
    "description": "Description goes here",
    "author": "FLEB (a.k.a. SuperFLEB)",
    "version": (0, 0, 1),
    "blender": (3, 4, 0),
    "location": "View3D > Object",
    "warning": "DO NOT ACTIVATE! This extension allows unsafe Python code execution, and should not be used until that is mitigated", # used for warning icon and text in addons panel
    "doc_url": "https://github.com/SuperFLEB/blender_tell_me_why",
    "tracker_url": "https://github.com/SuperFLEB/blender_tell_me_why/issues",
    "support": "COMMUNITY",
    # Categories:
    # 3D View, Add Curve, Add Mesh, Animation, Compositing, Development, Game Engine, Import-Export, Lighting, Material,
    # Mesh, Node, Object, Paint, Physics, Render, Rigging, Scene, Sequencer, System, Text Editor, UV, User Interface
    "category": "Object",
}


menus: list[tuple[str, Callable]] = []

# Registerable modules have a REGISTER_CLASSES list that lists all registerable classes in the module
registerable_modules = [
    wm_props,
    explanation,
    trust_op,
    preferences_panel,
    n_panel,
]


def register() -> None:
    for c in addon.get_registerable_classes(registerable_modules):

        # Attempt to clean up if the addon broke during registration.
        try:
            bpy.utils.unregister_class(c)
        except RuntimeError:
            pass
        bpy.utils.register_class(c)
        if hasattr(c, 'post_register') and callable(c.post_register):
            c.post_register()
        print("Tell Me Why registered class:", c)
    for prop_name, prop_def in wm_props.WM_PROPS.items():
        print("Tell Me Why registered WM property: ", prop_name, prop_def)
        PropDefClass = prop_def[0]
        setattr(bpy.types.WindowManager, prop_name, PropDefClass(**prop_def[1]))
    addon.register_menus(menus)


def unregister() -> None:
    for prop_name, prop_def in wm_props.WM_PROPS.items():
        delattr(bpy.types.WindowManager, prop_name)
    addon.unregister_menus(menus)
    for m in menus[::-1]:
        getattr(bpy.types, m[0]).remove(m[1])
    for c in addon.get_registerable_classes(registerable_modules)[::-1]:
        try:
            bpy.utils.unregister_class(c)
            if hasattr(c, 'post_unregister') and callable(c.post_unregister):
                c.post_unregister()
        except RuntimeError:
            pass


if __name__ == "__main__":
    register()
