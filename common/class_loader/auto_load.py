import importlib
import inspect
import pkgutil
import typing
from pathlib import Path

import bpy

__all__ = (
    "init",
    "register",
    "unregister",
    "add_properties",
    "remove_properties",
)

from ..types.framework import ExpandableUi, is_extension

blender_version = bpy.app.version

modules = None
ordered_classes = None
frame_work_classes = None


def init():
    global modules
    global ordered_classes
    global frame_work_classes
    # notice here, the path root is the root of the project
    modules = get_all_submodules(Path(__file__).parent.parent.parent)
    ordered_classes = get_ordered_classes_to_register(modules)
    frame_work_classes = get_framework_classes(modules)


def register():
    for cls in ordered_classes:
        bpy.utils.register_class(cls)

    for module in modules:
        if module.__name__ == __name__:
            continue
        if hasattr(module, "register"):
            module.register()

    for cls in frame_work_classes:
        register_framework_class(cls)

def unregister():
    for cls in reversed(ordered_classes):
        bpy.utils.unregister_class(cls)

    for module in modules:
        if module.__name__ == __name__:
            continue
        if hasattr(module, "unregister"):
            module.unregister()

    for cls in frame_work_classes:
        unregister_framework_class(cls)


# Import modules
#################################################

def get_all_submodules(directory):
    return list(iter_submodules(directory))


def iter_submodules(path):
    import_as_extension = is_extension()
    for name in sorted(iter_submodule_names(path)):
        if import_as_extension:
            yield importlib.import_module("..." + name, __package__)
        else:
            yield importlib.import_module("." + name, path.name)


def iter_submodule_names(path, root=""):
    for _, module_name, is_package in pkgutil.iter_modules([str(path)]):
        if is_package:
            sub_path = path / module_name
            sub_root = root + module_name + "."
            yield from iter_submodule_names(sub_path, sub_root)
        else:
            yield root + module_name


# Find classes to register
#################################################

def get_ordered_classes_to_register(modules):
    return toposort(get_register_deps_dict(modules))


def get_framework_classes(modules):
    base_types = get_framework_base_classes()
    all_framework_classes = set()
    for cls in get_classes_in_modules(modules):
        if any(base in base_types for base in cls.__mro__[1:]):
            all_framework_classes.add(cls)
    return all_framework_classes


def get_register_deps_dict(modules):
    my_classes = set(iter_my_classes(modules))
    my_classes_by_idname = {cls.bl_idname: cls for cls in my_classes if hasattr(cls, "bl_idname")}

    deps_dict = {}
    for cls in my_classes:
        deps_dict[cls] = set(iter_my_register_deps(cls, my_classes, my_classes_by_idname))
    return deps_dict


def iter_my_register_deps(cls, my_classes, my_classes_by_idname):
    yield from iter_my_deps_from_annotations(cls, my_classes)
    yield from iter_my_deps_from_inheritance(cls, my_classes)
    yield from iter_my_deps_from_parent_id(cls, my_classes_by_idname)


def iter_my_deps_from_annotations(cls, my_classes):
    for value in typing.get_type_hints(cls, {}, {}).values():
        dependency = get_dependency_from_annotation(value)
        if dependency is not None:
            if dependency in my_classes:
                yield dependency


def iter_my_deps_from_inheritance(cls, my_classes):
    for base_cls in cls.__mro__[1:]:
        if base_cls in my_classes:
            yield base_cls


def get_dependency_from_annotation(value):
    if blender_version >= (2, 93):
        if isinstance(value, bpy.props._PropertyDeferred):
            return value.keywords.get("type")
    else:
        if isinstance(value, tuple) and len(value) == 2:
            if value[0] in (bpy.props.PointerProperty, bpy.props.CollectionProperty):
                return value[1]["type"]
    return None


def iter_my_deps_from_parent_id(cls, my_classes_by_idname):
    if bpy.types.Panel in cls.__mro__[1:]:
        parent_idname = getattr(cls, "bl_parent_id", None)
        if parent_idname is not None:
            parent_cls = my_classes_by_idname.get(parent_idname)
            if parent_cls is not None:
                yield parent_cls


def iter_my_classes(modules):
    base_types = get_register_base_types()
    for cls in get_classes_in_modules(modules):
        if any(base in base_types for base in cls.__mro__[1:]):
            if not getattr(cls, "is_registered", False):
                yield cls


def get_classes_in_modules(modules):
    classes = set()
    for module in modules:
        for cls in iter_classes_in_module(module):
            classes.add(cls)
    return classes


def iter_classes_in_module(module):
    for value in module.__dict__.values():
        if inspect.isclass(value):
            yield value


def get_register_base_types():
    return set(getattr(bpy.types, name) for name in [
        "Panel", "Operator", "PropertyGroup",
        "AddonPreferences", "Header", "Menu",
        "Node", "NodeSocket", "NodeTree",
        "UIList", "RenderEngine",
        "Gizmo", "GizmoGroup",
    ])


def get_framework_base_classes():
    return {ExpandableUi}


# Find order to register to solve dependencies
#################################################

def toposort(deps_dict):
    sorted_list = []
    sorted_values = set()
    while len(deps_dict) > 0:
        unsorted = []
        # class with no dependencies
        independent = []
        for value, deps in deps_dict.items():
            if len(deps) == 0:
                independent.append(value)
            else:
                unsorted.append(value)

        # sort no dependencies by _reg_order
        independent.sort(key=lambda x: getattr(x, "_reg_order", float('inf')))
        # add to sorted list
        for value in independent:
            sorted_list.append(value)
            sorted_values.add(value)

        deps_dict = {value: deps_dict[value] - sorted_values for value in unsorted}
    return sorted_list


def register_framework_class(cls):
    if issubclass(cls, ExpandableUi):
        if hasattr(bpy.types, cls.target_id):
            if cls.expand_mode == "APPEND":
                getattr(bpy.types, cls.target_id).append(cls.draw)
            elif cls.expand_mode == "PREPEND":
                getattr(bpy.types, cls.target_id).prepend(cls.draw)
            else:
                raise ValueError(f"Invalid expand_mode: {cls.expand_mode}")
        else:
            print(f"Warning: Target ID not found: {cls.target_id}")


def unregister_framework_class(cls):
    if issubclass(cls, ExpandableUi):
        if hasattr(bpy.types, cls.target_id):
            getattr(bpy.types, cls.target_id).remove(cls.draw)


# support adding properties in a declarative way
def add_properties(property_dict: dict[typing.Any, dict[str, typing.Any]]):
    for cls, properties in property_dict.items():
        for name, prop in properties.items():
            setattr(cls, name, prop)


# support removing properties in a declarative way
def remove_properties(property_dict: dict[typing.Any, dict[str, typing.Any]]):
    for cls, properties in property_dict.items():
        for name in properties.keys():
            if hasattr(cls, name):
                delattr(cls, name)
