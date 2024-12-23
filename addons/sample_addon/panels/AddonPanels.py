import bpy

from ..config import __addon_name__
from ..operators.AddonOperators import ExampleOperator
from ....common.i18n.i18n import i18n
from ....common.types.framework import reg_order


class BasePanel(object):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ExampleAddon"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True


@reg_order(0)
class ExampleAddonPanel(BasePanel, bpy.types.Panel):
    bl_label = "Example Addon Side Bar Panel"
    bl_idname = "SCENE_PT_sample"

    def draw(self, context: bpy.types.Context):
        addon_prefs = context.preferences.addons[__addon_name__].preferences

        layout = self.layout

        layout.label(text=i18n("Example Functions") + ": " + str(addon_prefs.number))
        layout.prop(addon_prefs, "filepath")
        layout.separator()

        row = layout.row()
        row.prop(addon_prefs, "number")
        row.prop(addon_prefs, "boolean")

        layout.operator(ExampleOperator.bl_idname)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return True


# This panel will be drawn after ExampleAddonPanel since it has a higher order value
@reg_order(1)
class ExampleAddonPanel2(BasePanel, bpy.types.Panel):
    bl_label = "Example Addon Side Bar Panel"
    bl_idname = "SCENE_PT_sample2"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.label(text="Second Panel")
        layout.operator(ExampleOperator.bl_idname)
