import bpy
from ..props import variable as variable_props
from ..lib import pkginfo
from ..lib import addon as addon_lib, util
from . import n_panel, variables_uilist

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, variable_props, addon_lib, util, n_panel, variables_uilist):
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


class TMYPrefsPanel(bpy.types.AddonPreferences):
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

REGISTER_CLASSES = [TMYPrefsPanel]
