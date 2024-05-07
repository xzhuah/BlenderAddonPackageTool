import atexit
import os
import re
import shutil
import subprocess
from datetime import datetime
from os import listdir
from os.path import isfile, isdir

from common.io.FileManagerClient import read_utf8, write_utf8
from common.io.FileManagerClient import search_files

# The name of current active addon to be created, tested or released
ACTIVE_ADDON = "sample_addon"

# The path of the blender executable
BLENDER_EXE_PATH = "C:/software/general/Blender/Blender3.5/blender.exe"
# The path of the blender addon folder
BLENDER_ADDON_PATH = "C:/software/general/Blender/Blender3.5/3.5/scripts/addons/"

# The files to be ignored when release the addon
IGNORE_FILES = [".idea", "venv", "main.py", "release.py", "test.py", "create.py", "requirements.txt",
                ".git", ".gitignore",
                "README.md", ]

# The default release dir
DEFAULT_RELEASE_DIR = "../addon_release/"

# The default test release dir
TEST_RELEASE_DIR = "../addon_test/"

addon_namespace_pattern = re.compile("^[a-zA-Z]+[a-zA-Z0-9_]*$")

# The framework use this pattern to find the import module within the workspace
import_module_pattern = re.compile("from ([a-zA-Z0-9_.]+) import (.+)")


def new_addon(addon_name):
    if not bool(addon_namespace_pattern.match(addon_name)):
        print("InValid addon_name:", addon_name, "Please name it as a python package name")
        return
    shutil.copytree("./addons/sample_addon", f"./addons/{addon_name}")
    config = read_utf8(f"./addons/{addon_name}/config.py").replace("sample_addon", addon_name)
    write_utf8(f"./addons/{addon_name}/config.py", config)


def test_addon(addon_name):
    init_file = get_init_file_path(addon_name)
    start_test(init_file, addon_name)


def get_init_file_path(addon_name):
    # addon_name is the name defined in addon's config.py
    target_init_file = None
    for folder in os.listdir("./addons"):
        config_file = os.path.join("./addons", folder, "config.py")
        if os.path.exists(config_file):
            content = read_utf8(config_file).replace(" ", "")
            if f"__addon_name__=\"{addon_name}\"" in content:
                target_init_file = os.path.join("./addons", folder, "__init__.py")
                break
    assert target_init_file is not None and os.path.exists(
        target_init_file), f"Addon {addon_name} not found, please make sure config.py and __init__.py is correctly set for your addon."

    return target_init_file


def start_test(init_file, addon_name):
    addon_path = release_addon(init_file, addon_name, with_timestamp=False,
                               release_dir=TEST_RELEASE_DIR)
    executable_path = os.path.join(os.path.dirname(addon_path), addon_name)
    print("executable_path:", executable_path)

    test_addon_path = os.path.join(BLENDER_ADDON_PATH, addon_name)
    if os.path.exists(test_addon_path):
        shutil.rmtree(test_addon_path)
    shutil.copytree(executable_path, test_addon_path)

    def exit_handler():
        if os.path.exists(test_addon_path):
            shutil.rmtree(test_addon_path)

    atexit.register(exit_handler)

    try:
        subprocess.call([BLENDER_EXE_PATH, "--python-expr", f"import bpy\n"
                                                            f"bpy.ops.preferences.addon_enable(module=\"{addon_name}\")"])
    finally:
        exit_handler()


def release_addon(target_init_file, addon_name, with_timestamp=False, release_dir=DEFAULT_RELEASE_DIR):
    if not release_dir.startswith("../"):
        release_dir = "../" + release_dir
    if not bool(addon_namespace_pattern.match(addon_name)):
        print("InValid addon_name:", addon_name, "Please name it as a python package name")
        return
    content = read_utf8(target_init_file)
    write_utf8("__init__.py", content)

    if not release_dir.endswith("/"):
        release_dir += "/"
    if not os.path.exists(release_dir):
        os.mkdir(release_dir)

    # remove the folder if already exists
    release_folder = release_dir + addon_name
    if os.path.exists(release_folder):
        shutil.rmtree(release_folder)
    os.mkdir(release_folder)

    # copy useful file to the release dir
    for f in listdir("./"):
        if f not in IGNORE_FILES:
            # if file created time is not later than the timestamp
            if isfile("./" + f):
                shutil.copy(f, release_folder + "/" + f)
            elif isdir("./" + f):
                shutil.copytree("./" + f + "/", release_folder + "/" + f)

    remove_unnecessary_modules(release_folder)
    enhance_import_for_py_files(release_folder)

    real_addon_name = "{addon_name}_{timestamp}".format(addon_name=release_folder,
                                                        timestamp=datetime.now().strftime(
                                                            "%Y%m%d_%H%M%S")) if with_timestamp else "{addon_name}".format(
        addon_name=release_folder)

    # zip the addon
    zip_folder(release_folder, real_addon_name)
    released_addon_path = os.path.abspath(os.path.join(release_dir, real_addon_name) + ".zip")
    print("Add on released:", released_addon_path)
    return released_addon_path


def remove_unnecessary_modules(release_folder):
    add_on_entry_py = release_folder + "/" + "__init__.py"
    all_py_modules = find_all_py_modules(release_folder)

    un_visited_py_file = []
    visited_py_file = set()

    un_visited_py_file.append(add_on_entry_py)
    while len(un_visited_py_file) > 0:
        next_py_file = un_visited_py_file.pop()
        necessary_py_files = get_necessary_py_file_path(release_folder, next_py_file, all_py_modules)
        for py_file in necessary_py_files:
            if py_file not in visited_py_file:
                un_visited_py_file.append(py_file)
        visited_py_file.add(next_py_file)

    all_py_files = search_files(release_folder, {".py"})
    for py_file in all_py_files:
        if py_file not in visited_py_file:
            os.remove(py_file)

    remove_pyc_files(release_folder)

    removed_path = 1
    while removed_path > 0:
        removed_path = remove_empty_folders(release_folder)


# pyc files are auto generated when import, need to be removed before release
def remove_pyc_files(release_folder: str):
    all_pyc_file = search_files(release_folder, {"pyc"})
    for pyc_file in all_pyc_file:
        os.remove(pyc_file)


def get_necessary_py_file_path(root_folder: str, py_file_path: str, all_py_modules: set) -> list:
    if not py_file_path.startswith(root_folder):
        py_file_path = root_folder + "/" + py_file_path
    content = read_utf8(py_file_path)
    necessary_py_files = set()
    for module_path in import_module_pattern.finditer(content):
        import_module_path = module_path.groups()[0]
        import_module_name = module_path.groups()[1]

        if import_module_path in all_py_modules:
            # 3 possible related files
            module_file_path = root_folder + "/" + import_module_path.replace(".", "/") + ".py"

            if os.path.exists(module_file_path):
                necessary_py_files.add(module_file_path)

            for module_name in import_module_name.split(","):
                if "\\" not in module_name:
                    import_file_path = root_folder + "/" + import_module_path.replace(".",
                                                                                      "/") + "/" + module_name.strip() + ".py"
                    if os.path.exists(import_file_path):
                        necessary_py_files.add(import_file_path)
                else:
                    print("Warning: some module files might not be packaged due to multi-line import, please check",
                          py_file_path)

            # do back trace
            par_module = root_folder + "/"
            for module in import_module_path.split("."):
                par_module += module + "/"
                possible_init_file = par_module + "__init__.py"
                if os.path.exists(possible_init_file):
                    necessary_py_files.add(possible_init_file)

    return necessary_py_files


def remove_empty_folders(root_path):
    all_folder_to_remove = []
    for root, dirnames, filenames in os.walk(root_path, topdown=False):
        for dirname in dirnames:
            dir_to_check = os.path.join(root, dirname)
            if not os.listdir(dir_to_check):
                all_folder_to_remove.append(dir_to_check)
    for folder in all_folder_to_remove:
        os.removedirs(folder)
    return len(all_folder_to_remove)


# Zip the folder in a way that blender can recognize it as an addon.
def zip_folder(target_root, output_zip_file):
    # remove the tailing / of target_root
    while target_root.endswith("/"):
        target_root = target_root[0:-1]
    shutil.make_archive(output_zip_file, 'zip', target_root + "/../", base_dir=os.path.basename(target_root))


def enhance_import_for_py_files(addon_dir: str):
    re.compile("from import ")
    namespace = os.path.basename(addon_dir)
    all_py_modules = find_all_py_modules(addon_dir)
    all_py_file = search_files(addon_dir, {".py"})
    for py_file in all_py_file:
        content = read_utf8(py_file)
        for module_path in import_module_pattern.finditer(content):
            original_module_path = module_path.groups()[0]
            if original_module_path in all_py_modules:
                content = content.replace("from " + original_module_path + " import",
                                          "from " + namespace + "." + original_module_path + " import")
        write_utf8(py_file, content)


def find_all_py_modules(root_dir: str) -> set:
    all_py_modules = set()
    all_py_file = search_files(root_dir, {".py"})
    for py_file in all_py_file:
        rel_path = str(os.path.relpath(py_file, root_dir))
        modules = rel_path.replace("\\", "/").replace("__init__.py", "").replace(".py", "").split("/")
        if len(modules[-1]) == 0:
            modules = modules[0:-1]

        module_name = ""
        for i in range(len(modules)):
            module_name += modules[i] + "."
            all_py_modules.add(module_name[0:-1])
    return all_py_modules
