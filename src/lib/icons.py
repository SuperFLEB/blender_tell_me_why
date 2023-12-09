from pathlib import Path
import bpy
import bpy.utils.previews

_icons = None
icons = {}
_builtin_icons = {ei.name: ei.value for ei in bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items}


def register_icons():
    global _icons, icons
    _icons = bpy.utils.previews.new()
    icon_files = Path(__file__).parents[1].joinpath("icons").glob("*.png")
    for icon_file in icon_files:
        stem = icon_file.stem
        new_icon = _icons.load(stem, str(icon_file), "IMAGE")
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
