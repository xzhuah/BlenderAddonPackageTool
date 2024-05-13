import importlib.util
import os.path
import subprocess
import sys
import re
import importlib.metadata


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def has_module(module_name):
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception as e:
        return False


def is_package_installed(package_name):
    try:
        importlib.metadata.version(package_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def install_if_missing(package):
    if not has_module(package):
        install(package)


def extract_float(text):
    pattern = r'[-+]?\d*\.?\d+'
    matches = re.findall(pattern, text)
    for match in matches[::-1]:
        return match
    return None


def install_fake_bpy(blender_path: str):
    blender_version = extract_float(blender_path)
    if blender_version is None:
        print("Blender version not found in path: " + blender_path)
        blender_version = "latest"
    desired_module = "fake-bpy-module-" + blender_version
    if has_module("bpy"):
        if not is_package_installed(desired_module):
            print("Your fake bpy module is different from the current blender version! You might need to update it.")
        return
    else:
        print("Installing fake bpy module for Blender version: " + blender_version)
        install(desired_module)


def default_blender_addon_path(blender_path: str):
    assert os.path.exists(blender_path) and blender_path.endswith(
        "blender.exe"), "Invalid blender path: " + blender_path + "! Please provide a valid blender path pointing to the blender.exe."
    blender_version = extract_float(blender_path)
    assert blender_version is not None, "Blender version not found in path: " + blender_path
    return os.path.join(os.path.dirname(blender_path), blender_version, "scripts", "addons")
