import bpy


def is_extension():
    # Blender extension package starts with "bl_ext."
    # https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html#extensions-and-namespace
    return str(__package__).startswith("bl_ext.")


# DO NOT use framework classes in __init__.py

class ExpandableUi:
    # ID of the target panel.menu to be expanded to
    target_id: str
    # mode of expansion, either "PREPEND" or "APPEND"
    expand_mode: str = "APPEND"

    def draw(self, context: bpy.types.Context):
        raise NotImplementedError("draw method must be implemented")
