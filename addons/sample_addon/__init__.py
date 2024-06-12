import bpy

from addons.sample_addon.config import __addon_name__
from addons.sample_addon.i18n.dictionary import dictionary
from common.class_loader import auto_load
from common.class_loader.auto_load import add_properties, remove_properties
from common.i18n.dictionary import common_dictionary
from common.i18n.i18n import load_dictionary

# Add-on info
bl_info = {
    "name": "Basic Add-on Sample",
    "author": "[You name]",
    "blender": (3, 5, 0),
    "version": (0, 0, 1),
    "description": "This is a template for building addons",
    "warning": "",
    "doc_url": "[documentation url]",
    "tracker_url": "[contact email]",
    "support": "COMMUNITY",
    "category": "3D View"
}

_addon_properties = {}


# You may declare properties like following, framework will automatically add and remove them.
# Do not define your own property group class in the __init__.py file. Define it in a separate file and import it here.
# 注意不要在__init__.py文件中自定义PropertyGroup类。请在单独的文件中定义它们并在此处导入。
# _addon_properties = {
#     bpy.types.Scene: {
#         "property_name": bpy.props.StringProperty(name="property_name"),
#     },
# }

# Best practice: Please do not define Blender classes in the __init__.py file.
# Define them in separate files and import them here. This is because the __init__.py file would be copied during
# addon packaging, and defining Blender classes in the __init__.py file may cause unexpected problems.
# 建议不要在__init__.py文件中定义Blender相关的类。请在单独的文件中定义它们并在此处导入它们。
# __init__.py文件在代码打包时会被复制，在__init__.py文件中定义Blender相关的类可能会导致意外的问题。
def register():
    print("registering")
    # Register classes
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)

    # Internationalization
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)

    print("{} addon is installed.".format(bl_info["name"]))


def unregister():
    # Internationalization
    bpy.app.translations.unregister(__addon_name__)
    # unRegister classes
    auto_load.unregister()
    remove_properties(_addon_properties)

    print("{} addon is uninstalled.".format(bl_info["name"]))
