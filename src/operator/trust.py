from typing import Set
import bpy
import secrets
from datetime import datetime
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
    bl_label = "Trust this file's formulas for this session"
    bl_options = set()

    def execute(self, context) -> Set[str]:
        prefs = context.preferences.addons[package_name].preferences
        return {'FINISHED'}


class ReportFormulas(Operator):
    bl_idname = "tell_me_why.report_formulas"
    bl_label = "Formula Report"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        formulas, formula_hash = trust_lib.get_formulas_and_hash()
        formulas = formulas if formulas else ["(No formulas found)"]
        formula_report = "    " + "\n    ".join(formulas)
        now = datetime.today().strftime('%a, %x %X')
        report = bpy.data.texts.new(f"Formula Report {now}.txt")
        report.use_fake_user = False

        title = f"Tell Me Why addon Value and Formula Report, generated {now}"

        line_len = 100

        body = "\n".join(util.wordwrap("This report can inform your decision whether or not to trust running formulas "
                                       "on this Blender file. If any of these appear to be anything except numbers or "
                                       "values or a way to calculate them, you should NOT trust this file. "
                                       "Withholding trust will not cause the file to work or render differently. It "
                                       "will only prevent automatic calculation of formulas to compare or set node "
                                       "input values.",
                                       line_len))
        body += "\n\n"
        body += "\n".join(util.wordwrap("If you did not generate this report, you should create another one. If you "
                                        "do not have the \"Tell Me Why\" addon installed, you don't have anything at "
                                        "all to worry about, because all this only relatees to that addon.", line_len))
        body += "\n\n"
        body += "\n".join(util.wordwrap("These are the formulas that have been found in this file:", line_len))
        body += "\n"

        debug_info = f"Debug: Hash value {formula_hash}\n(this information is unique to your configuration)"

        # report.write(f"{title}\n{'=' * len(title)}\n\n{body}\n{formula_report}\n\n{debug_info}")
        return {'FINISHED'}


REGISTER_CLASSES = [TrustSession, ReportFormulas]
