import bpy
from ..panel import n_panel
from ..lib import node as node_lib

if "_LOADED" in locals():
    import importlib

    for mod in (node_lib,):  # list all imports here
        importlib.reload(mod)
_LOADED = True


def annotations_indicator(self, context):
    layout = self.layout
    active_node = context.active_node
    active_node = active_node if active_node and active_node.select else None
    node_state = node_lib.get_node_explanation_state(active_node)

    box = layout.box()
    if node_state.has_explained:
        box.popover(n_panel.NODE_PT_TellMeWhyPopover.bl_idname, text="Tell Me Why", icon="INFO")
    else:
        box.popover(n_panel.NODE_PT_TellMeWhyPopover.bl_idname, text="No Annotations")
