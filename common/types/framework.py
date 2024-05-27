import bpy


# DO NOT use framework classes in __init__.py

class ExpandableUi:
    target_id: str
    mode: str = "APPEND"

    def draw(self, context: bpy.types.Context):
        raise NotImplementedError("draw method must be implemented")
