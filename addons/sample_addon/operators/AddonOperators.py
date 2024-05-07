# Created by Xinyu Zhu on 11/23/2022, 10:50 PM
import bpy
from addons.sample_addon.config import __addon_name__
from addons.sample_addon.preference.AddonPreferences import ExampleAddonPreferences


# This Example Operator will scale up the selected object
class ExampleOperator(bpy.types.Operator):
    bl_idname = "object.example_ops"
    bl_label = "ExampleOperator"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {"UNDO_GROUPED"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        addon_prefs = bpy.context.preferences.addons[__addon_name__].preferences
        assert isinstance(addon_prefs, ExampleAddonPreferences)
        # use operator
        # bpy.ops.transform.resize(value=(2, 2, 2))

        # manipulate the scale directly
        context.active_object.scale *= addon_prefs.number
        return {'FINISHED'}
