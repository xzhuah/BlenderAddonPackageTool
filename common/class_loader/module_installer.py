# Notice: Please do not use functions in this file for developing your Blender Addons, this file is for internal use of
# the framework, it contains some modules that Blender officially prohibits using in Addons. Such as sys
# 注意：请不要在Blender中使用此文件中的函数,此文件用于框架内部使用,包含了一些Blender官方禁止在插件中使用的模块 如sys
import importlib.metadata
import importlib.util
import os
import platform
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


def get_blender_version(blender_exe_path):
    try:
        # Run the Blender executable with --version
        result = subprocess.run(
            [blender_exe_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Check if the process was successful
        if result.returncode == 0:
            output = result.stdout
            # Parse the version from the output
            for line in output.splitlines():
                if line.startswith("Blender"):
                    # Extract version number
                    return line.split()[1]  # e.g., "3.6.2"
        else:
            print("Error running Blender:", result.stderr)
    except Exception as e:
        print(f"An error occurred when trying to determine Blender version: {e}")
    return None


def extract_blender_version(blender_exe_path: str):
    """Extract the first two version numbers from the Blender executable path."""
    version_str = get_blender_version(blender_exe_path)
    try:
        return ".".join(version_str.split(".")[0:2])
    except Exception as e:
        print(f"An error occurred when trying to extract Blender version from {version_str}: {e}")
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


def normalize_blender_path_by_system(blender_path: str):
    if is_mac():
        if blender_path.endswith(".app"):
            blender_path = os.path.join(blender_path, "Contents/MacOS/Blender")
    return blender_path


def default_blender_addon_path(blender_path: str):
    blender_path = normalize_blender_path_by_system(blender_path)
    blender_version = extract_blender_version(blender_path)
    assert blender_version is not None, "Can not detect Blender version with " + blender_path + "!"
    if is_windows() or is_linux():
        new_path = os.path.join(os.path.dirname(blender_path), blender_version, "scripts", "addons_core")
        if os.path.exists(new_path):
            return new_path
        return os.path.join(os.path.dirname(blender_path), blender_version, "scripts", "addons")
    elif is_mac():
        user_path = os.path.expanduser("~")
        return os.path.join(user_path, f"Library/Application Support/Blender/{blender_version}/scripts/addons")
    else:
        raise Exception(
            "This Framework is currently not compatible with your operating system! Please use Windows, MacOS or Linux.")


def is_windows():
    return platform.system() == "Windows"


def is_linux():
    return platform.system() == "Linux"


def is_mac():
    return platform.system() == "Darwin"
