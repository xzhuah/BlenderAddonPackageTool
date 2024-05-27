import bpy


# DO NOT use framework classes in __init__.py

class ExpandableUi:
    # ID of the target panel.menu to be expanded to
    target_id: str
    # mode of expansion, either "PREPEND" or "APPEND"
    expand_mode: str = "APPEND"

    def draw(self, context: bpy.types.Context):
        raise NotImplementedError("draw method must be implemented")
