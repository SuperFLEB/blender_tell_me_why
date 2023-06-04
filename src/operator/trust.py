from typing import Set
import bpy
import secrets
from datetime import datetime
from time import time
from bpy.types import Operator, NodeSocket, PropertyGroup
from bpy.props import PointerProperty, StringProperty, BoolProperty, FloatProperty, IntProperty, CollectionProperty
from ..lib import pkginfo
from ..lib import node as node_lib
from ..lib import trust as trust_lib
from ..lib import util

package_name = pkginfo.package_name()

if "_LOADED" in locals():
    import importlib

    for mod in (node_lib, trust_lib, util, pkginfo):  # list all imports here
        importlib.reload(mod)
_LOADED = True


class TrustSession(Operator):
    """Initialize Tell Me Why data for a given node"""
    bl_idname = "tell_me_why.trust_session"
    bl_label = "Trust this file for now"
    bl_description = "Trust TMY formulas in this file now, but ask again after the file is closed or reloaded"
    bl_options = set()

    @classmethod
    def poll(cls, context):
        if trust_lib.is_file_trusted():
            poll_messages = {
                'ALL': "Trust has been enabled globally",
                'CLEAN_LOAD': "The file initially contained no formulas",
                'SESSION': "The file has already been trusted for this session",
                'HASH': "This file is already trusted"
            }
            cls.poll_message_set(poll_messages.get(trust_lib.get_trust_reason(), "This file is being trusted"))
            return False

        if not trust_lib.are_formulas_enabled():
            cls.poll_message_set('Trusted formula evaluation has been disabled')
            return False
        if not trust_lib.has_formulas():
            cls.poll_message_set('This file contains no formulas')
            return False
        return True

    def execute(self, context) -> Set[str]:
        try:
            trust_lib.trust_session()
            return {'FINISHED'}
        except trust_lib.AllTrustDisabledException:
            self.report({'ERROR'}, 'Formulas and trust features have been disabled. Cannot trust the file.')
            return {'CANCELLED'}


class TrustFile(Operator):
    bl_idname = "tell_me_why.trust_file"
    bl_label = "Always trust this file"
    bl_description = "Trust TMY formulas in this file, and continue to trust the file in the future. This trust can be managed in the Preferences panel for the Tell Me Why addon."
    bl_options = set()

    user_approved_save: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        if not trust_lib.are_formulas_enabled():
            cls.poll_message_set('Trusted formula evaluation has been disabled')
            return False
        if trust_lib.is_file_trusted(only_explicit_trust=True):
            cls.poll_message_set('This file is already trusted')
            return False
        if not trust_lib.has_formulas():
            cls.poll_message_set('This file contains no formulas')
            return False
        return True

    def execute(self, context):
        # If they don't have "Auto-Save Preferences", we need to honor that and ask first
        if not (bpy.context.preferences.use_preferences_save or self.user_approved_save):
            bpy.ops.tell_me_why.confirm_trust_file()
            return {'CANCELLED'}

        # Reset this for the next time
        self.user_approved_save = False

        # This is faster than hashing and checking, so try it first
        if trust_lib.is_file_trusted(only_explicit_trust=True):
            self.report({'ERROR'}, 'This file is already trusted')

        try:
            trust_lib.save_trust_hash(trust_if_exists=True)
        except trust_lib.NoFormulasException:
            self.report({'ERROR'}, 'No formulas. Nothing to trust.')
            return {'CANCELLED'}
        except trust_lib.AlreadyTrustedException:
            self.report({'WARNING'}, 'This file (or one with all the same formulas) is already trusted')
            return {'FINISHED'}
        except trust_lib.AllTrustDisabledException:
            self.report({'ERROR'}, 'Formulas and trust features have been disabled. Cannot trust the file.')
            return {'CANCELLED'}

        bpy.ops.wm.save_userpref()

        return {'FINISHED'}


class ConfirmTrustFile(Operator):
    bl_idname = "tell_me_why.confirm_trust_file"
    bl_label = "Generate Formula Report"
    bl_options = set()
    bl_description = "Confirm that the user wants to save the trust addition"

    def execute(self, context):
        def confirm(dialog, _) -> None:
            dialog.layout.label(text="Your Preferences will be saved in order to apply this setting.", icon="INFO")
            trust_file_operator = dialog.layout.operator(TrustFile.bl_idname, text="Continue and Save Preferences")
            trust_file_operator.user_approved_save = True

        bpy.context.window_manager.popup_menu(confirm, title=TrustFile.bl_label)
        return {'FINISHED'}


class ReportFormulas(Operator):
    bl_idname = "tell_me_why.report_formulas"
    bl_label = "Generate Formula Report"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Generate a report of all the formulas in this Blender file, so you can determine whether you want to trust it"

    @classmethod
    def write_report(cls) -> bpy.types.Text:
        formulas = trust_lib.get_all_formulas()
        formula_hash = trust_lib.hash_formulas()
        formulas = formulas if formulas else ["(No formulas found)"]
        formula_report = "    " + "\n    ".join(formulas)
        now = datetime.today().strftime('%a, %x %X')
        report = bpy.data.texts.new(f"Formula Report {now}.txt")
        report.use_fake_user = False

        title = f"Tell Me Why addon Value and Formula Report, generated {now}"

        line_len = 100

        body = "\n".join(util.wordwrap("This report can inform your decision whether or not to trust running formulas "
                                       "on this Blender file. If any of these appear to be anything except numbers, "
                                       "values, or a way to calculate them, you should NOT trust this file. "
                                       "Withholding trust will not cause the file to work or render differently. It "
                                       "will only prevent automatic calculation of formulas in the Tell Me Why addon.",
                                       line_len))
        body += "\n\n"
        body += "\n".join(util.wordwrap("If you did not generate this report, you should create another one. If you "
                                        "do not have the \"Tell Me Why\" addon installed, you don't have anything at "
                                        "all to worry about, because all this only relatees to that addon.", line_len))
        body += "\n\n"
        body += "\n".join(util.wordwrap("These are the formulas that have been found in this file:", line_len)) + "\n"
        body += "-" * line_len + "\n"

        debug_info = "-" * line_len + "\n"
        debug_info += f"Debug: Hash value {formula_hash}\n(this information is unique to your configuration)"

        report.write(f"{title}\n{'=' * len(title)}\n\n{body}\n{formula_report}\n\n{debug_info}")
        return report

    def execute(self, context):
        report = self.write_report()
        report_name = report.name

        def message(menu, _) -> None:
            para = menu.layout.column()
            para.scale_y = 0.8

            msg = f"A report has been output to the \"{report_name}\" Text object. View it in your \"Scripting\" view (or other Text view) and verify that you trust all formulas in this file."
            msg2 = "If you trust this file's formulas, you can trust the file and allow running formulas, temporarily or permanently, using the \"File > Tell Me Why\" menu."

            lines = util.wordwrap(msg, 120) + [""] + util.wordwrap(msg2, 120) + [""]

            para.label(text=lines[0], icon="INFO")
            for line in lines[1:]:
                para.label(text=line, icon="BLANK1")

        bpy.context.window_manager.popup_menu(message, title="Report Generated")

        return {'FINISHED'}


class LaunchAddonPrefs(Operator):
    bl_idname = "tell_me_why.trust_launch_prefs"
    bl_label = "Manage Trust Options"
    bl_options = set()
    bl_description = "Open the Tell Me Why addon's options page, where you can manage trust (and other) options."

    def execute(self, context):
        bpy.ops.screen.userpref_show()
        bpy.context.preferences.active_section = 'ADDONS'
        bpy.data.window_managers["WinMan"].addon_search = "Tell Me Why"
        return {'FINISHED'}


REGISTER_CLASSES = [TrustSession, TrustFile, ConfirmTrustFile, ReportFormulas, LaunchAddonPrefs]
