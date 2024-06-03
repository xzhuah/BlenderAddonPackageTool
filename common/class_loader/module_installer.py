import importlib.metadata
import importlib.util
import os.path
import re
import subprocess
import sys


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


def extract_blender_version(blender_exe_path: str):
    folder_path = os.path.dirname(blender_exe_path)
    for version in ["2.93", "3.0", "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "4.0", "4.1", "4.2"]:
        if os.path.exists(os.path.join(folder_path, version)):
            return version
    pattern = r'\d+\.?\d+'
    matches = re.findall(pattern, blender_exe_path)
    for match in matches[::-1]:
        if os.path.exists(os.path.join(folder_path, match)):
            return match
        elif len(match) > 3 and os.path.exists(os.path.join(folder_path, match[:3])):
            return match[:3]
    return None


def install_fake_bpy(blender_path: str):
    blender_version = extract_blender_version(blender_path)
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
        try:
            install(desired_module)
        except Exception as e:
            if desired_module != "fake-bpy-module-latest":
                print(
                    "Failed to install fake bpy module for Blender version: " + blender_version + "! Trying to install the latest version.")
                install("fake-bpy-module-latest")


def default_blender_addon_path(blender_path: str):
    assert os.path.exists(blender_path) and blender_path.endswith(
        "blender.exe"), "Invalid blender path: " + blender_path + "! Please provide a valid blender path pointing to the blender.exe."
    blender_version = extract_blender_version(blender_path)
    assert blender_version is not None, "Blender version not found in path: " + blender_path
    new_path = os.path.join(os.path.dirname(blender_path), blender_version, "scripts", "addons_core")
    if os.path.exists(new_path):
        return new_path
    return os.path.join(os.path.dirname(blender_path), blender_version, "scripts", "addons")
