# MIT License
#
# Copyright (c) [2024] [Xinyu Zhu]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import atexit, os, re, shutil, subprocess, time, threading
from pathlib import Path
from datetime import datetime
from os import listdir
from os.path import isfile, isdir

from common.class_loader.module_installer import install_if_missing, install_fake_bpy, default_blender_addon_path

# The name of current active addon to be created, tested or released
ACTIVE_ADDON = "sample_addon"

# The path of the blender executable. Blender2.93 is the minimum version required
# Blender可执行文件的路径，Blender2.93是所需的最低版本
BLENDER_EXE_PATH = "C:/software/general/Blender/Blender3.5/blender.exe"

# The path of the blender addon folder
# Blender插件文件夹的路径
BLENDER_ADDON_PATH = default_blender_addon_path(BLENDER_EXE_PATH)
# You can override the default path by setting the path manually
# 您可以通过手动设置路径来覆盖默认插件安装路径
# BLENDER_ADDON_PATH = "C:/software/general/Blender/Blender3.5/3.5/scripts/addons/"

# The files to be ignored when release the addon
# 发布插件时要忽略的文件
IGNORE_FILES = [".idea", "venv", "main.py", "release.py", "test.py", "create.py", "requirements.txt",
                ".git", ".gitignore",
                "README.md", ]

# The default release dir. Must not within the current workspace
# 插件发布的默认目录，不能在当前工作空间内
DEFAULT_RELEASE_DIR = "../addon_release/"

# The default test release dir. Must not within the current workspace
# 测试插件发布的默认目录，不能在当前工作空间内
TEST_RELEASE_DIR = "../addon_test/"

addon_namespace_pattern = re.compile("^[a-zA-Z]+[a-zA-Z0-9_]*$")

# The framework use this pattern to find the import module within the workspace
import_module_pattern = re.compile("from ([a-zA-Z0-9_.]+) import (.+)")

__addon_md5__signature__ = "addon.txt"

install_if_missing("watchdog")
install_fake_bpy(BLENDER_EXE_PATH)

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from common.io.FileManagerClient import read_utf8, write_utf8, get_md5_folder
from common.io.FileManagerClient import search_files


def new_addon(addon_name):
    if os.path.exists(f"./addons/{addon_name}") or not bool(addon_namespace_pattern.match(addon_name)):
        print("InValid addon_name:", addon_name, "Please name it as a python package name")
        return
    shutil.copytree("./addons/sample_addon", f"./addons/{addon_name}")

    all_py_file = search_files(f"./addons/{addon_name}", {".py"})
    for py_file in all_py_file:
        content = read_utf8(py_file).replace("sample_addon", addon_name)
        write_utf8(py_file, content)


def test_addon(addon_name, enable_watch=True):
    init_file = get_init_file_path(addon_name)
    start_test(init_file, addon_name, enable_watch=enable_watch)


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


def get_addon_original_package_name(addon_name):
    init_path = get_init_file_path(addon_name)
    return os.path.basename(os.path.dirname(init_path))


# https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040
start_up_command = """
import bpy
from bpy.app.handlers import persistent
import os
import sys
existing_addon_md5 = ""
bpy.ops.preferences.addon_enable(module="{addon_name}")

def watch_update_tick():
    global existing_addon_md5
    if os.path.exists("{addon_signature}"):
        with open("{addon_signature}", "r") as f:
            addon_md5 = f.read()
        if existing_addon_md5 == "":
            existing_addon_md5 = addon_md5
        elif existing_addon_md5 != addon_md5:
            print("Addon file changed, start to update the addon")
            bpy.ops.preferences.addon_disable(module="{addon_name}")
            all_modules = sys.modules
            all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them
            for k,v in all_modules.items():
                if k.startswith("{addon_name}"):
                    del sys.modules[k]
            bpy.ops.preferences.addon_enable(module="{addon_name}")
            existing_addon_md5 = addon_md5
            print("Addon updated")
    return 1.0

@persistent
def register_watch_update_tick(dummy):
    print("Watching for addon update...")
    bpy.app.timers.register(watch_update_tick)

register_watch_update_tick(None)
bpy.app.handlers.load_post.append(register_watch_update_tick)
"""


def start_test(init_file, addon_name, enable_watch=True):
    update_addon_for_test(init_file, addon_name)
    test_addon_path = os.path.join(BLENDER_ADDON_PATH, addon_name)

    if not enable_watch:
        def exit_handler():
            if os.path.exists(test_addon_path):
                shutil.rmtree(test_addon_path)

        atexit.register(exit_handler)
        try:
            subprocess.call(
                [BLENDER_EXE_PATH, "--python-expr",
                 f"import bpy\nbpy.ops.preferences.addon_enable(module=\"{addon_name}\")"])
        finally:
            exit_handler()
        return

    # start_watch_for_update(init_file, addon_name)
    stop_event = threading.Event()
    thread = threading.Thread(target=start_watch_for_update, args=(init_file, addon_name, stop_event))
    thread.start()

    def exit_handler():
        stop_event.set()
        thread.join()
        if os.path.exists(test_addon_path):
            shutil.rmtree(test_addon_path)

    atexit.register(exit_handler)

    python_script = start_up_command.format(addon_name=addon_name,
                                            addon_signature=os.path.join(test_addon_path,
                                                                         __addon_md5__signature__).replace("\\", "/"))

    try:
        subprocess.call([BLENDER_EXE_PATH, "--python-expr", python_script])
    finally:
        exit_handler()


def release_addon(target_init_file, addon_name, with_timestamp=False, release_dir=DEFAULT_RELEASE_DIR, need_zip=True):
    if not bool(addon_namespace_pattern.match(addon_name)):
        print("InValid addon_name:", addon_name, "Please name it as a python package name")
        return
    content = read_utf8(target_init_file)
    write_utf8("__init__.py", content)

    if not os.path.isdir(release_dir):
        os.mkdir(release_dir)

    # remove the folder if already exists
    release_folder = os.path.join(release_dir, addon_name)
    if os.path.exists(release_folder):
        shutil.rmtree(release_folder)
    os.mkdir(release_folder)

    # copy useful file to the release dir
    for f in listdir("./"):
        if f not in IGNORE_FILES:
            # if file created time is not later than the timestamp
            if isfile(f):
                shutil.copy(f, os.path.join(release_folder, f))
            elif isdir(f):
                shutil.copytree(f, os.path.join(release_folder, f))

    remove_unnecessary_modules(release_folder, get_addon_original_package_name(addon_name))
    enhance_import_for_py_files(release_folder)

    real_addon_name = "{addon_name}_{timestamp}".format(addon_name=release_folder,
                                                        timestamp=datetime.now().strftime(
                                                            "%Y%m%d_%H%M%S")) if with_timestamp else "{addon_name}".format(
        addon_name=release_folder)

    released_addon_path = os.path.abspath(os.path.join(release_dir, real_addon_name) + ".zip")
    # zip the addon
    if need_zip:
        zip_folder(release_folder, real_addon_name)
        print("Add on released:", released_addon_path)

    os.remove("__init__.py")

    return released_addon_path


def remove_unnecessary_modules(release_folder, addon_original_package_name):
    add_on_entry_py = os.path.join(release_folder, "__init__.py")
    all_py_modules = find_all_py_modules(release_folder)

    un_visited_py_file = []
    visited_py_file = set()

    all_addon_py_files = search_files(os.path.join(release_folder, "addons", addon_original_package_name), {".py"})
    un_visited_py_file.append(add_on_entry_py)
    un_visited_py_file.extend(all_addon_py_files)

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
        py_file_path = os.path.join(root_folder, py_file_path)
    content = read_utf8(py_file_path)
    necessary_py_files = set()
    for module_path in import_module_pattern.finditer(content):
        import_module_path = module_path.groups()[0]
        import_module_name = module_path.groups()[1]

        if import_module_path in all_py_modules:
            # 3 possible related files
            module_file_path = os.path.join(root_folder, import_module_path.replace(".", os.path.sep) + ".py")

            if os.path.exists(module_file_path):
                necessary_py_files.add(module_file_path)

            for module_name in import_module_name.split(","):
                if "\\" not in module_name:
                    import_file_path = os.path.join(root_folder, *import_module_path.split("."),
                                                    module_name.strip() + ".py")
                    if os.path.exists(import_file_path):
                        necessary_py_files.add(import_file_path)
                else:
                    print("Warning: some module files might not be packaged due to multi-line import, please check",
                          py_file_path)

            # do back trace
            par_module = root_folder + os.path.sep
            for module in import_module_path.split("."):
                par_module += module + os.path.sep
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
    shutil.make_archive(output_zip_file, 'zip', Path(target_root).parent, base_dir=os.path.basename(target_root))


def enhance_import_for_py_files(addon_dir: str):
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
        modules = rel_path.replace("__init__.py", "").replace(".py", "").split(os.path.sep)
        if len(modules[-1]) == 0:
            modules = modules[0:-1]

        module_name = ""
        for i in range(len(modules)):
            module_name += modules[i] + "."
            all_py_modules.add(module_name[0:-1])
    return all_py_modules


class FileUpdateHandler(FileSystemEventHandler):
    def __init__(self):
        super(FileUpdateHandler, self).__init__()
        self.has_update = False

    def on_any_event(self, event):
        source_path = event.src_path
        if source_path.endswith(".py"):
            self.has_update = True

    def clear_update(self):
        self.has_update = False


def start_watch_for_update(init_file, addon_name, stop_event: threading.Event):
    path = "."
    event_handler = FileUpdateHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
            if event_handler.has_update:
                print("Addon updated, start to update the test addon")
                try:
                    update_addon_for_test(init_file, addon_name)
                    event_handler.clear_update()
                except Exception as e:
                    print(e)
                    print(
                        "Addon updated failed: Please make sure no other process is using the addon folder. You might need to restart the test to update the addon in Blender.")
        print("Stop watching for update...")

    except KeyboardInterrupt:
        observer.stop()
        observer.join()


def update_addon_for_test(init_file, addon_name):
    addon_path = release_addon(init_file, addon_name, with_timestamp=False,
                               release_dir=TEST_RELEASE_DIR, need_zip=False)
    executable_path = os.path.join(os.path.dirname(addon_path), addon_name)

    test_addon_path = os.path.join(BLENDER_ADDON_PATH, addon_name)
    if os.path.exists(test_addon_path):
        shutil.rmtree(test_addon_path)
    shutil.copytree(executable_path, test_addon_path)

    # write an MD5 to the addon folder to inform the addon content has been changed
    addon_md5 = get_md5_folder(executable_path)
    write_utf8(os.path.join(test_addon_path, __addon_md5__signature__), addon_md5)
