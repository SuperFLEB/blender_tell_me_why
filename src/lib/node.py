from typing import Iterable, Callable
import bpy
from bpy.types import NodeSocket



def default_value_string(socket: NodeSocket, unprintable: str = "---", float_fix: int = 3):
    def fix(val):
        return f"{{0:.{float_fix}f}}".format(val)

    if not hasattr(socket, 'default_value'):
        return unprintable
    # There are probably some fundamental misunderstandings in here. Need to verify this when I get a chance.
    if socket.type in ['VALUE', 'INT']:
        return fix(socket.default_value)
    if socket.type == 'STRING':
        return str(socket.default_value)
    if socket.type in ['VECTOR', 'RGBA']:
        return '(' + ', '.join([fix(el) for el in socket.default_value]) + ')'
    if socket.type in ['SHADER', 'OBJECT', 'IMAGE', 'TEXTURE', 'MATERIAL', 'COLLECTION']:
        return socket.type.title() + ": " + socket.default_value.name
    if socket.type == 'BOOLEAN':
        return "True" if socket.default_value else "False"
    return unprintable

