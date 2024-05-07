import bpy

from common.class_loader import auto_load
from addons.sample_addon.config import __addon_name__
from addons.sample_addon.i18n.dictionary import dictionary
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


def register():
    print("registering")
    # Register classes
    auto_load.init()
    auto_load.register()

    # Internationalization
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)

    print("{} addon is installed.".format(bl_info["name"]))


def unregister():
    # Internationalization
    bpy.app.translations.unregister(__addon_name__)
    # unRegister classes
    auto_load.unregister()

    print("{} addon is uninstalled.".format(bl_info["name"]))
