import bpy

"""Get all sockets from all node types, and dump a documentation starter python file.
Written late, accidentally deleted, rewritten late, and poorly. Don't judge me."""

node_types = ['ShaderNode', 'CompositorNode', 'GeometryNode', 'TextureNode']

inputs = {}
outputs = {}

for nt in node_types:
    ng = bpy.data.node_groups.new(type=f"{nt}Tree",name=f"{nt} Group")
    subs = [s for s in dir(bpy.types) if s.startswith(nt) and s != nt]
    subs += [s for s in dir(bpy.types) if s.startswith("FunctionNode") and s != nt]
    for s in subs:
        new_node = None
        try:
            new_node = ng.nodes.new(type=s)
        except BaseException as e:
            print("ERR!", e)
        if new_node:
            for i in new_node.inputs:
                iname = i.name
                if inputs.get(iname, None):
                    inputs[iname]['users'].append(s)
                else:
                    inputs[iname] = {'users': [s], 'first': i}
            for o in new_node.outputs:
                oname = o.name
                if outputs.get(oname, None):
                    outputs[oname]['users'].append(s)
                else:
                    outputs[oname] = {'users': [s], 'first': o}

export = "input_default_docs = {\n"
for name, socket in inputs.items():
    users = ", ".join([u for u in socket['users']])
    export += f'    "{name}": "Undocumented {socket["first"].type} input", # {users}\n'
export +="}\n\n"

export += "output_default_docs = {\n"
for name, socket in outputs.items():
    users = ", ".join([u for u in socket['users']])
    export += f'    "{name}": "Undocumented {socket["first"].type} output",  # {users}\n'
export +="}\n\n"

print(export)
txt = bpy.data.texts.new(name="export.py")
txt.write(export)

