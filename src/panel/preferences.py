import bpy

from ..lib import addon as addon_lib
from ..lib import pkginfo
from ..lib import util
from ..panel import n_panel

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, addon_lib, util,):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()


def get_location(self):
    return self.get("value", 0)


def set_location(self, value):
    changed = self.get("value", 0) != value
    self["value"] = value
    if changed:
        n_panel.update_panel_category()


class TellMeWhyPrefsPanel(bpy.types.AddonPreferences):
    bl_idname = package_name

    start_expanded: bpy.props.BoolProperty(
        name="Always show all sockets",
        description="Show sockets you have not added explanations to when viewing a node, without needing to click "
                    '"Show All/Add More"',
        default=False
    )

    n_panel_location: bpy.props.EnumProperty(
        name="N-Panel location",
        description="Where should the Tell Me Why panel be located?",
        items=[
            ("Tell Me Why", 'In a "Tell Me Why" tab', "Put the panel in its own tab"),
            ("Node", 'In the "Node" tab', "Put the panel after other items in the Node tab"),
        ],
        get=get_location,
        set=set_location
    )

    def draw(self, context) -> None:
        layout = self.layout
        layout.prop(self, "start_expanded")
        layout.prop(self, "n_panel_location")


REGISTER_CLASSES = [TellMeWhyPrefsPanel]
