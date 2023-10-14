import bpy
from bpy.types import Operator, NodeSocket, PropertyGroup
from bpy.props import StringProperty, BoolProperty, FloatProperty, IntProperty, CollectionProperty

def set_split_components(self, value):
    # Collapse existing formulas to a tuple if we are turning off split_components and all are used
    if not (value or [c for c in self.components if not (c and c["use_formula"])]):
        formulas = [c["formula"] for c in self.components]
        for c in self.components[1:]:
            c["formula"] = ""
            c["description"] = ""
            c["use_formula"] = False
        self.components[0]["formula"] = f"({', '.join(formulas)})"
    else:
        for c in self.components:
            c["formula"] = ""
            c["description"] = ""
            c["use_formula"] = False
    self["split_components"] = value


def get_split_components(self):
    return self.get("split_components", False)


class ComponentValueExplanation(PropertyGroup):
    """A formula (or value). The formula may return a tuple or a single value, depending on whether the Explanation
    is single-value, split, or combined"""
    description: StringProperty(name="description", default="")
    use_formula: BoolProperty(name="Use Value/Formula", default=False)
    formula: StringProperty(name="formula", default="")
    # TODO: Make this an ENUM type
    type: StringProperty(name="type", default="float")
    # If the value has been collapsed to a single formula (in the Explanation properties),
    # the formula is expected to return an Iterable of this length. Usually "1" for split components.
    length: IntProperty(name="vector length", min=1, max=4, default=1)


bpy.utils.register_class(ComponentValueExplanation)

class ExplanationVariable(PropertyGroup):
    """Defined variables used in Explanations"""
    name: StringProperty(name="name")
    value: FloatProperty(name="value")
    description: StringProperty(name="description")


bpy.utils.register_class(ExplanationVariable)


class Explanation(PropertyGroup):
    active: BoolProperty(name="active", default=False)
    description: StringProperty(name="Description", default="")
    components: CollectionProperty(type=ComponentValueExplanation)
    variables: CollectionProperty(type=ExplanationVariable)
    split_components: BoolProperty(name="Split components", default=True, set=set_split_components,
                                   get=get_split_components)

    @classmethod
    def post_register(cls):
        NodeSocket.explanation = bpy.props.PointerProperty(type=cls, name="explanation")


REGISTER_CLASSES = [Explanation]
