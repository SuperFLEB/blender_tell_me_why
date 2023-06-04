import bpy
from bpy.types import Menu
from ..operator import trust
from ..lib import addon
from ..lib import trust as trust_lib
from ..lib import pkginfo

package_name = pkginfo.package_name()

if "_LOADED" in locals():
    import importlib

    for mod in (trust, addon,):  # list all imports here
        importlib.reload(mod)
_LOADED = True


class FileTrustSubmenu(Menu):
    bl_idname = 'TELL_ME_WHY_MT_file_trust_menu'
    bl_label = 'Tell Me Why'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = "EXEC_DEFAULT"

        prefs = bpy.context.preferences.addons[package_name].preferences

        trust_explainers = {
            'ALL': "Trust has been enabled globally",
            'CLEAN_LOAD': "This file was new or contained no formulas on load, so trust is unnecessary",
            'SESSION': "The file has already been trusted for this session",
            'HASH': "This file is already trusted",
            'UNTRUSTED': "This file is not trusted"
        }

        trust_all = prefs['trust_all'] and prefs['really_trust_all']

        if trust_all:
            layout.label(text="You are currently trusting all formulas from all files! This is unsafe!", icon="ERROR")
            layout.operator(trust.LaunchAddonPrefs.bl_idname, text="Manage Settings...", icon="PREFERENCES")
        elif trust_lib.is_file_trusted():
            layout.label(text=trust_explainers.get(trust_lib.get_trust_reason()), icon="INFO")
        else:
            layout.label(text="You are not currently trusting this file", icon="INFO")

        layout.separator()

        layout.operator(trust.TrustSession.bl_idname)
        layout.operator(trust.TrustFile.bl_idname)
        layout.separator()
        layout.operator(trust.ReportFormulas.bl_idname, text="Should I trust this file?", icon="QUESTION")
        layout.operator(trust.LaunchAddonPrefs.bl_idname, text="Manage Trust Preferences...", icon="PREFERENCES")


REGISTER_CLASSES = [FileTrustSubmenu]
