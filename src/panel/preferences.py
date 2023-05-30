import bpy

from ..lib import pkginfo

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo,):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()


def get_trust_all(self) -> bool:
    return self.get('trust_all', False)


def set_trust_all(self, value):
    self['trust_all'] = bool(value)
    self['really_trust_all'] = False


class TellMeWhyPrefsPanel(bpy.types.AddonPreferences):
    bl_idname = package_name
    trust_all: bpy.props.BoolProperty(
        name="Trust all formulas from all files",
        description="Trust all formulas from all files. This is probably not recommended.",
        get=lambda self: self.get('trust_all', False),
        set=set_trust_all
    )
    really_trust_all: bpy.props.BoolProperty(
        name="I understand \"Trust all formulas\" is really dangerous",
        description="Trust all formulas even though this is a huge security backdoor and any malicious Blender file could have full reign of my system."
    )
    trust_identity: bpy.props.StringProperty(name="Trust Identity Token", description="A randomly generated token used to make spoofing formula hashes more difficult.", default="")

    def draw(self, context) -> None:
        layout = self.layout
        layout.prop(self, 'trust_all')
        if self.trust_all:
            layout.prop(self, 'really_trust_all')
        layout.label(text=f"Identity Token: " + self.get('trust_identity', "(Not created yet)"))


REGISTER_CLASSES = [TellMeWhyPrefsPanel]
