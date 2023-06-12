from typing import Set
import bpy
from bpy.types import Operator
from bpy.props import IntProperty, CollectionProperty
from ..lib import util
from ..lib import pkginfo
from ..lib import trust as trust_lib

package_name = pkginfo.package_name()

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, util,):  # list all imports here
        importlib.reload(mod)
_LOADED = True


class TrustListDelete(Operator):
    """Initialize Tell Me Why data for a given node"""
    bl_idname = "tell_me_why.trust_list_delete"
    bl_label = "Remove Selected"
    bl_description = "Remove selected item from the Trusted Files list"
    bl_options = set()

    delete_index: IntProperty()

    @classmethod
    def poll(cls, context):
        return bool(bpy.context.preferences.addons[package_name].preferences.trust_hashes)

    def execute(self, context):
        prefs = bpy.context.preferences.addons[package_name].preferences
        selected_hash = prefs.trust_hashes[prefs.active_trust_hash].formula_hash
        prefs.trust_hashes.remove(prefs.active_trust_hash)
        if trust_lib.forget_if_hash(selected_hash):
            print(f"Trust revoked for the currently-open file because {selected_hash} was deleted")
        else:
            print(f"Trust was not revoked for the currently-open file, because it was not the one deleted")
        return {'FINISHED'}

REGISTER_CLASSES = [TrustListDelete]