from ...common.types.framework import is_extension

# https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html#extensions-and-namespace
# This is the unique package name of the addon, it is different from the add-on name in bl_info.
# This name is used to identify the add-on in python code. It should also be the same to the package name of the add-on.
__addon_name__ = ".".join(__package__.split(".")[0:3]) if is_extension() else __package__.split(".")[0]
