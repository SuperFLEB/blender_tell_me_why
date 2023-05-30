import bpy
from ..lib import formula as formula_lib

def my_handler(scene):
    print("Pre-save handler. Should be calculating and storing the new formula hash")


bpy.app.handlers.save_pre.append(my_handler)

