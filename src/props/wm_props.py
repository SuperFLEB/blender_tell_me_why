import bpy


class SocketState(bpy.types.PropertyGroup):
    edit_mode: bpy.props.BoolProperty(default=False)
    rgba: bpy.props.FloatVectorProperty(subtype="COLOR", size=4)


class TellMeWhyGlobals(bpy.types.PropertyGroup):
    socket_states: bpy.props.CollectionProperty(type=SocketState)
    show_unexplained: bpy.props.BoolProperty(default=False)
    variable_selected_index: bpy.props.IntProperty()


WM_PROPS: dict[str, tuple[bpy.types.AnyType, dict[str, any]]] = {
    "tell_me_why_globals": (bpy.props.PointerProperty, {"type": TellMeWhyGlobals}),
}

REGISTER_CLASSES = [SocketState, TellMeWhyGlobals]
