import bpy
import datetime
from bpy.types import PropertyGroup, UIList
from bpy.props import StringProperty, IntProperty
from ..lib import pkginfo
from ..lib import addon as addon_lib
from ..lib import util

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo, addon_lib, util,):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()


def get_trust_all(self) -> bool:
    return self.get('trust_all', False)


def set_trust_all(self, value):
    self['trust_all'] = bool(value)
    self['really_trust_all'] = False


class TrustHash(bpy.types.PropertyGroup):
    formula_hash: StringProperty(name="Formula Hash", description="A representation (hash) of all the formulas and variables in the trusted file")
    formula_hash_version: IntProperty(name="Hash Version", description="An incrementing version number indicating compatibility", default=1)
    filename: StringProperty(name="Filename", description="File name when the hash was stored")
    orig_filename: StringProperty(name="Filename", description="Name of the file when it was first trusted")
    # This is going to be epoch time stored as a string. Blender's IntProperty is only 32-bit and 2038 is getting closer
    timestamp: StringProperty(name="Time", description="Time the hash was stored")


bpy.utils.register_class(TrustHash)

class TrustHashesUIList(UIList):
    """Trusted files list"""
    bl_label = "Trusted Files"
    bl_idname = "TELL_ME_WHY_UL_trust_list"

    def filter_items(self, context, data, propname):
        property_values = getattr(data, propname)

        def sortable_value(raw_value: TrustHash):
            return f"{raw_value.orig_filename.ljust(256)}{raw_value.timestamp}"

        return [], util.uilist_sort(property_values, sortable_value)

    def draw_item(self, context, layout, data, item, iocon, active_data, active_propname, index) -> None:
        layout.label(text=item.filename)
        layout.label(text=item.orig_filename)
        layout.label(text=item.formula_hash)
        timestamp = item.timestamp
        time_display = datetime.datetime.fromtimestamp(int(item.timestamp), datetime.timezone.utc).astimezone().strftime("%x %X") if timestamp else "<no timestamp>"
        layout.label(text=time_display)


class TellMeWhyPrefsPanel(bpy.types.AddonPreferences):
    bl_idname = package_name

    start_expanded: bpy.props.BoolProperty(
        name="Always show all sockets",
        description='Show sockets you have not added explanations to when viewing a node, without needing to click "Show All/Add More"',
        default=False
    )

    enable_trusted_formulas: bpy.props.BoolProperty(
        name="Enable Trusted Formulas",
        description='Allow formulas in trusted files to run. If disabled, no formulas will be evaluated.',
        default=True
    )

    trust_all: bpy.props.BoolProperty(
        name="Trust all formulas from all files",
        description="Trust all formulas from all files. This is probably not recommended.",
        get=lambda self: self.get('trust_all', False),
        set=set_trust_all
    )

    really_trust_all: bpy.props.BoolProperty(
        name='I understand "Trust all formulas" may be unsafe. Really trust all formulas.',
        description="I won't blame the author of this addon if there's a bug and a malicious formula slips through"
    )

    trust_hashes: bpy.props.CollectionProperty(type=TrustHash)

    active_trust_hash: bpy.props.IntProperty()

    trust_identity: bpy.props.StringProperty(name="Trust Identity Token", description="A randomly generated token used to make spoofing formula hashes more difficult.", default="")

    def draw(self, context) -> None:
        layout = self.layout
        layout.prop(self, 'start_expanded')
        layout.prop(self, 'enable_trusted_formulas')
        self.layout.template_list(
            listtype_name=TrustHashesUIList.bl_idname,
            list_id=TrustHashesUIList.bl_idname + "@Preferences",
            dataptr=self,
            propname="trust_hashes",
            active_dataptr=self,
            active_propname="active_trust_hash",
            rows=3,
            sort_lock=True
        )
        layout.prop(self, 'trust_all')
        if self.trust_all:
            addon_lib.multiline_label(context, layout, text="While care has been taken to prevent malicious formulas from having any effect, bugs may still be a possibility, and running untrusted formulas may be unsafe", icon="ERROR")
            layout.prop(self, 'really_trust_all')
        layout.label(text=f"Identity Token: " + self.get('trust_identity', "(Not created yet)"))


REGISTER_CLASSES = [TellMeWhyPrefsPanel, TrustHashesUIList]
