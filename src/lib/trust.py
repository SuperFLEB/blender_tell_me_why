from typing import Callable
import bpy
import secrets
from hashlib import sha256
import json
from . import pkginfo

if "_LOADED" in locals():
    import importlib

    for mod in (pkginfo,):  # list all imports here
        importlib.reload(mod)
_LOADED = True

package_name = pkginfo.package_name()


class TrustException(Exception):
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


def get_all_formulas():
    nodes = _find_formula_nodes()
    formulas = set()
    for node in nodes:
        explanations = [s['explanation'] for s in list(node.inputs) + list(node.outputs) if 'explanation' in s and 'components' in s.explanation]
        for explanation in explanations:
            formulas |= {c['formula'] for c in explanation['components'] if 'formula' in c}

    formulas = [f for f in formulas if f != ""]
    return formulas


def get_formulas_and_hash() -> tuple[list[str], str]:
    formulas = list(get_all_formulas())
    # Formulas have to be concatenated or compiled in an unambiguous way that does not allow the user to create
    # equivalent text by concatenating formulas. JSON conversion serves that role.
    formulas_dump = json.dumps(formulas)
    identity = get_trust_identity()
    hashed = sha256(f"{identity}{formulas_dump}".encode('utf-8')).hexdigest()
    return formulas, hashed


def get_trust_identity():
    prefs = bpy.context.preferences.addons[package_name].preferences
    if not prefs.get('trust_identity', None):
        prefs['trust_identity'] = secrets.token_urlsafe(64)
    return prefs['trust_identity']


def generate_formula_hash():
    identity = get_trust_identity()
    

def is_trusted() -> bool:
    prefs = bpy.context.preferences.addons[package_name].preferences
    identity = get_trust_identity()

    # Check for "Trust all" in prefs
    if prefs['trust_all'] and prefs['really_trust_all']:
        return True

    # Check for session trust
    if bpy.context.window_manager.get(f"{identity}_trust_session", False):
        return True

    # Check for hash trust
    print("HASH TRUST IS NOT YET IMPLEMENTED!")

    return False

