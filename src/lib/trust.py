from typing import Callable
import bpy
import secrets
from time import time
from hashlib import sha256
import json
from . import pkginfo

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo,):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()


class TrustApplicationException(Exception):
    pass


class NoFormulasException(TrustApplicationException):
    pass


class AlreadyTrustedException(TrustApplicationException):
    pass


class AllTrustDisabledException(TrustApplicationException):
    pass


def _find_formula_nodes(seek_fn: Callable[[bpy.types.bpy_prop_collection], bool] = None):
    # If we're in seek mode, we're not in collect mode
    collect = not seek_fn

    # Only these locations are scanned for nodes when creating the formula report. Other node types, such as those created
    # in newer versions of Blender, should not be allowed to run, because the user cannot verify them.
    node_locations = {
        "nodes": ['node_groups'],
        "node_tree.nodes": ['materials', 'lights', 'scenes'],
    }

    nodes = set()
    for loc in node_locations['nodes']:
        for thing in getattr(bpy.data, loc, []):
            if collect:
                nodes |= set(thing.nodes)
            if seek_fn and seek_fn(thing.nodes):
                return True

    for loc in node_locations['node_tree.nodes']:
        for thing in getattr(bpy.data, loc, []):
            if hasattr(thing, 'node_tree') and hasattr(thing.node_tree, 'nodes') and len(thing.node_tree.nodes):
                if collect:
                    nodes |= set(thing.node_tree.nodes)
                if seek_fn and seek_fn(thing.node_tree.nodes):
                    return True
    if not collect:
        return False
    return nodes


def is_trustable_node(node: bpy.types.NodeInternal):
    return _find_formula_nodes(lambda nodes: nodes.get(node.name, None) == node)


# Use "first_only" when you only want to know if there _are_ formulas
def get_all_formulas(first_only: bool = False) -> list[str]:
    nodes = _find_formula_nodes()
    formulas = set()
    for node in nodes:
        explanations = [s['explanation'] for s in list(node.inputs) + list(node.outputs) if 'explanation' in s and 'components' in s.explanation]
        for explanation in explanations:
            for component in explanation['components']:
                if 'formula' in component and component['formula'] != "":
                    if first_only:
                        return [component['formula']]
                    formulas.add(component['formula'])
    formulas = [f for f in formulas if f != ""]
    return formulas


def has_formulas() -> bool:
    return bool(get_all_formulas(first_only=True))


def hash_formulas():
    # Formulas have to be concatenated or compiled in an unambiguous way that does not allow the user to create
    # equivalent text by concatenating formulas. JSON conversion serves that role.
    formulas = get_all_formulas()

    if not formulas:
        raise NoFormulasException("No need to trust a file with no formulas")

    formulas_json = json.dumps(formulas)
    # TODO: Include vars dumps
    identity = get_trust_identity()
    hashed = sha256(f"{identity}{formulas_json}".encode('utf-8')).hexdigest()
    return hashed


def get_trust_identity():
    prefs = bpy.context.preferences.addons[package_name].preferences
    if not prefs.get('trust_identity', None):
        prefs['trust_identity'] = secrets.token_urlsafe(64)
    return prefs['trust_identity']


def is_file_trusted(only_explicit_trust: bool = False) -> bool:
    prefs = bpy.context.preferences.addons[package_name].preferences
    tmy = bpy.context.window_manager.tell_me_why_globals

    if not are_formulas_enabled():
        return False

    if not only_explicit_trust:
        # Check for "Trust all" in prefs
        if prefs.trust_all is True and prefs.really_trust_all is True:
            return True

        # Check for "Trust this file for now" session trust
        if tmy.trust_session is True:
            return True

    # Check if this file was trusted or known on load
    if tmy.get('trusted_file_hash', None):
        return True

    return False


def get_trust_reason() -> str:
    """Get the reason this file was trusted, or "UNTRUSTED" if it is not trusted. For display only."""
    prefs = bpy.context.preferences.addons[package_name].preferences
    tmy = bpy.context.window_manager.tell_me_why_globals

    if not are_formulas_enabled():
        return 'UNTRUSTED'

    # Check for "Trust all" in prefs
    if prefs.trust_all is True and prefs.really_trust_all is True:
        return 'ALL'

    if tmy.trust_session and tmy.no_formulas_on_load:
        return 'CLEAN_LOAD'

    # Check for "Trust this file for now" session trust
    if tmy.trust_session is True:
        return 'SESSION'

    # Check if this file was trusted or known on load
    if tmy.get('trusted_file_hash', None):
        return 'HASH'

    return 'UNTRUSTED'


def trust_if_known() -> bool:
    """Hash the file's formulas and set the WindowManager "trusted_file_hash" if it matches a known trusted hash"""
    if not are_formulas_enabled():
        raise AllTrustDisabledException("Formulas are disabled. Cannot apply trust.")

    prefs = bpy.context.preferences.addons[package_name].preferences
    tmy = bpy.context.window_manager.tell_me_why_globals
    hashed = hash_formulas()

    for th in prefs.trust_hashes:
        if th.formula_hash == hashed:
            tmy.trusted_file_hash = th.formula_hash
            return True
    return False


def save_trust_hash(trust_if_exists=False) -> None:
    """Hash the file and save a trust hash to the user preferences"""
    if not are_formulas_enabled():
        raise AllTrustDisabledException("Formulas are disabled. Cannot apply trust.")

    prefs = bpy.context.preferences.addons[package_name].preferences
    tmy = bpy.context.window_manager.tell_me_why_globals

    hashed = hash_formulas()

    for th in [th for th in prefs.trust_hashes if th]:
        if th.formula_hash == hashed:
            if trust_if_exists:
                tmy.trusted_file_hash = hashed
            raise AlreadyTrustedException("Trust hash matches one already saved")

    filepath = bpy.context.blend_data.filepath
    filename = bpy.path.basename(filepath) if filepath else "<unsaved file>"
    timestamp = str(int(time()))

    trust_hash_object = prefs.trust_hashes.add()
    trust_hash_object.formula_hash = hashed
    print(f"Write {trust_hash_object.formula_hash} to THO.hashed")
    trust_hash_object.filename = filename
    print(f"Write {trust_hash_object.filename} to THO.filename")
    trust_hash_object.orig_filename = filename
    print(f"Write {trust_hash_object.orig_filename} to THO.orig_filename")
    trust_hash_object.timestamp = timestamp
    print(f"Write {trust_hash_object.timestamp} to THO.timestamp")

    tmy.trusted_file_hash = hashed


def trust_session(flag_no_formulas_on_load: bool = False):
    if not are_formulas_enabled():
        raise AllTrustDisabledException("Formulas are disabled. Cannot apply trust.")

    tmy = bpy.context.window_manager.tell_me_why_globals
    tmy.trust_session = True
    if flag_no_formulas_on_load:
        tmy.no_formulas_on_load = True


def trust_if_no_formulas():
    """If there are no formulas, trust the file for the session.
       This is okay, because the user can be assumed not to be a malicious actor."""
    if not are_formulas_enabled():
        raise AllTrustDisabledException("Formulas are disabled. Cannot apply trust.")

    if not has_formulas():
        trust_session(flag_no_formulas_on_load=True)


def are_formulas_enabled():
    prefs = bpy.context.preferences.addons[package_name].preferences
    return prefs.enable_trusted_formulas is True
