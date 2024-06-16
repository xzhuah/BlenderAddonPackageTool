import os

# This is the unique package name of the addon, it is different from the add-on name in bl_info.
# This name is used to identify the add-on in python code. It should also be the same to the package name of the add-on.
__addon_name__ = os.path.basename(os.path.dirname(__file__))
