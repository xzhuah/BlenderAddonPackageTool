import ast
import atexit
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from common.class_loader.module_installer import install_if_missing, install_fake_bpy
from common.io.FileManagerClient import search_files, read_utf8, write_utf8, is_subdirectory, get_md5_folder
from main import PROJECT_ROOT, BLENDER_ADDON_PATH, BLENDER_EXE_PATH, DEFAULT_RELEASE_DIR, TEST_RELEASE_DIR

install_if_missing("watchdog")
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

try:
    import tomllib
except ImportError:
    install_if_missing("toml")
    import toml

# Following variables are used internally in the framework according to some protocols defined by Blender or
# the framework itself. Do not change them unless you know what you are doing.
_addon_namespace_pattern = re.compile("^[a-zA-Z]+[a-zA-Z0-9_]*$")
_import_module_pattern = re.compile("from ([a-zA-Z_][a-zA-Z0-9_.]*) import (.+)")
_addon_md5__signature = "addon.txt"
_ADDON_MANIFEST_FILE = "blender_manifest.toml"
_WHEELS_PATH = "wheels"
# 默认使用的插件模板 不要轻易修改
_ADDON_TEMPLATE = "sample_addon"
_ADDONS_FOLDER = "addons"
_ADDON_ROOT = os.path.join(PROJECT_ROOT, _ADDONS_FOLDER)

install_fake_bpy(BLENDER_EXE_PATH)


def new_addon(addon_name: str):
    new_addon_path = os.path.join(_ADDON_ROOT, addon_name)
    if os.path.exists(new_addon_path):
        raise ValueError("Addon already exists: " + addon_name)
    if not bool(_addon_namespace_pattern.match(addon_name)):
        raise ValueError("Invalid addon name: " + addon_name + " Please name it as a python package name")
    shutil.copytree(os.path.join(_ADDON_ROOT, _ADDON_TEMPLATE), new_addon_path)

    all_template_file = search_files(new_addon_path, {".py", ".toml"})
    for py_file in all_template_file:
        content = read_utf8(py_file).replace(_ADDON_TEMPLATE, addon_name)
        write_utf8(py_file, content)


def test_addon(addon_name, enable_watch=True):
    init_file = get_init_file_path(addon_name)
    if not enable_watch:
        print('Do not auto reload addon when file changed')
    start_test(init_file, addon_name, enable_watch=enable_watch)


def get_init_file_path(addon_name):
    # addon_name is the name defined in addon's config.py
    target_init_file_path = os.path.join(_ADDON_ROOT, addon_name, "__init__.py")
    if not os.path.exists(target_init_file_path):
        raise ValueError(f"Release failed: Addon {addon_name} not found.")
    return target_init_file_path

# The following code will be injected into the blender python environment to enable hot reload
# https://devtalk.blender.org/t/plugin-hot-reload-by-cleaning-sys-modules/20040
start_up_command = """
import bpy
from bpy.app.handlers import persistent
import os
import sys
existing_addon_md5 = ""
try:
    bpy.ops.preferences.addon_enable(module="{addon_name}")
except Exception as e:
    print("Addon enable failed:", e)

def watch_update_tick():
    global existing_addon_md5
    if os.path.exists("{addon_signature}"):
        with open("{addon_signature}", "r") as f:
            addon_md5 = f.read()
        if existing_addon_md5 == "":
            existing_addon_md5 = addon_md5
        elif existing_addon_md5 != addon_md5:
            print("Addon file changed, start to update the addon")
            try:
                bpy.ops.preferences.addon_disable(module="{addon_name}")
                all_modules = sys.modules
                all_modules = dict(sorted(all_modules.items(),key= lambda x:x[0])) #sort them
                for k,v in all_modules.items():
                    if k.startswith("{addon_name}"):
                        del sys.modules[k]
                bpy.ops.preferences.addon_enable(module="{addon_name}")
            except Exception as e:
                print("Addon update failed:", e)
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
    test_addon_path = os.path.normpath(os.path.join(BLENDER_ADDON_PATH, addon_name))

    if not enable_watch:
        def exit_handler():
            if os.path.exists(test_addon_path):
                shutil.rmtree(test_addon_path)

        atexit.register(exit_handler)
        try:
            execute_blender_script(
                [BLENDER_EXE_PATH, "--python-use-system-env", "--python-expr",
                 f"import bpy\nbpy.ops.preferences.addon_enable(module=\"{addon_name}\")"], test_addon_path)
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
                                                                         _addon_md5__signature).replace("\\", "/"))

    try:
        execute_blender_script([BLENDER_EXE_PATH, "--python-use-system-env", "--python-expr", python_script],
                               test_addon_path)
    finally:
        exit_handler()


def execute_blender_script(args, addon_path):
    process = subprocess.Popen(args, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    try:
        for line in process.stderr:
            line: str
            if line.lstrip().startswith("File"):
                line = line.replace(addon_path, PROJECT_ROOT)
            sys.stderr.write(line)
    except KeyboardInterrupt:
        sys.stderr.write("interrupted, terminating the child process...\n")
    finally:
        process.terminate()
        process.wait()


def release_addon(target_init_file, addon_name, with_timestamp=False, release_dir=DEFAULT_RELEASE_DIR, need_zip=True,
                  with_version=False):
    # if release dir is under PROJECT_ROOT, it's not allowed
    if is_subdirectory(release_dir, PROJECT_ROOT):
        # 不要将插件发布目录设置在当前项目内
        raise ValueError("Invalid release dir:", release_dir,
                         "Please set a release/test dir outside the current workspace")

    if not bool(_addon_namespace_pattern.match(addon_name)):
        raise ValueError("InValid addon_name:", addon_name, "Please name it as a python package name")

    if not os.path.isdir(release_dir):
        Path(release_dir).mkdir(parents=True, exist_ok=True)

    # remove the folder if already exists
    release_folder = os.path.join(release_dir, addon_name)
    if os.path.exists(release_folder):
        shutil.rmtree(release_folder)
    os.mkdir(release_folder)
    shutil.copyfile(target_init_file, os.path.join(release_folder, "__init__.py"))
    # 将target_init_file同级的其他非py文件复制到发布目录 如 toml xml等可能跟插件有关的配置文件
    for file in os.listdir(os.path.dirname(target_init_file)):
        file_path = os.path.join(os.path.dirname(target_init_file), file)
        if os.path.isdir(file_path) or file.endswith(".py"):
            continue
        shutil.copy(file_path, release_folder)

    # 将插件文件夹复制到发布目录
    shutil.copytree(os.path.join(_ADDON_ROOT, addon_name), os.path.join(release_folder, _ADDONS_FOLDER, addon_name))
    shutil.copyfile(os.path.join(_ADDON_ROOT, "__init__.py"),
                    os.path.join(release_folder, _ADDONS_FOLDER, "__init__.py"))

    all_py_files = search_files(os.path.join(_ADDON_ROOT, addon_name), {".py"})
    # 对插件文件夹中的每一个py文件进行分析，找到每个py文件中依赖的其他py文件
    visited_py_files = set()
    for py_file in all_py_files:
        visited_py_files.add(os.path.abspath(py_file))
    # 注意不要漏掉__init__.py文件
    visited_py_files.add(os.path.abspath(os.path.join(_ADDON_ROOT, "__init__.py")))

    dependencies = find_all_dependencies(list(visited_py_files), PROJECT_ROOT)
    for dependency in dependencies:
        dependency = os.path.abspath(dependency)
        if dependency in visited_py_files:
            continue
        visited_py_files.add(dependency)
        target_path = os.path.join(release_folder, os.path.relpath(dependency, PROJECT_ROOT))
        if not os.path.exists(os.path.dirname(target_path)):
            os.makedirs(os.path.dirname(target_path))
        shutil.copy(dependency, os.path.join(release_folder, os.path.relpath(dependency, PROJECT_ROOT)))

    remove_pyc_files(release_folder)
    removed_path = 1
    while removed_path > 0:
        removed_path = remove_empty_folders(release_folder)

    enhance_import_for_py_files(release_folder)

    # include wheel files when need to be zipped
    if need_zip:
        addon_config_file = os.path.join(_ADDON_ROOT, addon_name, _ADDON_MANIFEST_FILE)
        if os.path.exists(addon_config_file):
            with open(addon_config_file, 'r', encoding='utf-8') as f:
                try:
                    addon_config = tomllib.loads(f.read())
                except Exception as e:
                    addon_config = toml.load(f)
                if "wheels" in addon_config:
                    wheel_files = addon_config["wheels"]
                    if len(wheel_files) > 0:
                        wheel_folder = os.path.join(release_folder, _WHEELS_PATH)
                        os.mkdir(wheel_folder)
                        for wheel_file in wheel_files:
                            wheel_source = os.path.join(PROJECT_ROOT, wheel_file)
                            if not os.path.exists(wheel_source):
                                raise ValueError("Wheel file not found:", wheel_source,
                                                 ". Please download the required wheel file to the wheels folder.")
                            shutil.copy(wheel_source, wheel_folder)

    real_addon_name = "{addon_name}".format(addon_name=release_folder)
    if with_version:
        bl_info = get_addon_info(target_init_file)
        if bl_info is not None:
            _version = '.'.join([str(x) for x in bl_info['version']])
        else:
            _version = 'None'
            print("fetch version info failed, set version to 'None' ")
        real_addon_name = f"{release_folder}_V{_version}"
    if with_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        real_addon_name = f"{real_addon_name}_{timestamp}"

    released_addon_path = os.path.abspath(os.path.join(release_dir, real_addon_name) + ".zip")
    # zip the addon
    if need_zip:
        zip_folder(release_folder, real_addon_name)
        print("Add on released:", released_addon_path)

    return released_addon_path


def get_addon_info(filename: str):
    file_content = read_utf8(filename)
    # match bl_info content in [addon]/__init__.py
    bl_info_pattern = r'bl_info\s*=\s*{(.+?)}\s*'

    match = re.search(bl_info_pattern, file_content, re.DOTALL)

    if match:
        bl_info_content = match.group(1).strip()
        bl_info_dict = eval('{' + bl_info_content + '}')
        return bl_info_dict
    else:
        print("bl_info not found in the file.")
        return None


# pyc files are auto generated, need to be removed before release
def remove_pyc_files(release_folder: str):
    all_pyc_file = search_files(release_folder, {"pyc"})
    for pyc_file in all_pyc_file:
        os.remove(pyc_file)


def remove_empty_folders(root_path):
    all_folder_to_remove = []
    for root, dirnames, filenames in os.walk(root_path, topdown=False):
        for dirname in dirnames:
            dir_to_check = os.path.join(root, dirname)
            if not os.listdir(dir_to_check):
                all_folder_to_remove.append(dir_to_check)
    for folder in all_folder_to_remove:
        shutil.rmtree(folder)
    return len(all_folder_to_remove)


# Zip the folder in a way that blender can recognize it as an addon.
def zip_folder(target_root, output_zip_file):
    shutil.make_archive(output_zip_file, 'zip', Path(target_root).parent, base_dir=os.path.basename(target_root))


def find_imported_modules(file_path):
    root = ast.parse(read_utf8(file_path), filename=file_path)

    imported_modules = set()
    for node in ast.walk(root):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module
                imported_modules.add(module_name)
            for alias in node.names:
                if node.module:
                    imported_modules.add(f"{node.module}.{alias.name}")
                else:
                    imported_modules.add(alias.name)

    return imported_modules


def resolve_module_path(module_name, base_path, project_root):
    if not module_name.endswith(".*"):
        # Handle import all
        module_path = module_name.replace('.', '/')
        module_path = os.path.join(project_root, module_path)
        if os.path.isdir(module_path):
            module_path = os.path.join(module_path, '__init__.py')
            return [module_path]
        elif os.path.isfile(module_path + '.py'):
            module_path = module_path + '.py'
            return [module_path]
        else:
            if "." not in module_name:
                # most likely a standard library module
                return []
            current_search_dir = os.path.dirname(base_path)
            while is_subdirectory(current_search_dir, project_root):
                module_path = module_name.replace('.', '/')
                module_path = os.path.join(current_search_dir, module_path)
                if os.path.isdir(module_path):
                    module_path = os.path.join(module_path, '__init__.py')
                    return [module_path]
                elif os.path.isfile(module_path + '.py'):
                    module_path = module_path + '.py'
                    return [module_path]
                current_search_dir = os.path.dirname(current_search_dir)
            return []
    else:
        module_name = module_name[:-2]
        module_path = module_name.replace('.', '/')
        possible_root_path = os.path.join(project_root, module_path)
        if os.path.isdir(possible_root_path):
            possible_root_path = os.path.join(possible_root_path, '__init__.py')
            return [possible_root_path]
        elif os.path.isfile(possible_root_path + '.py'):
            possible_root_path = possible_root_path + '.py'
            return [possible_root_path]
        else:
            current_search_dir = os.path.dirname(base_path)
            while is_subdirectory(current_search_dir, project_root):

                possible_root_path = os.path.join(current_search_dir, module_path)
                if os.path.isdir(possible_root_path):
                    possible_root_path = os.path.join(possible_root_path, '__init__.py')
                    return [possible_root_path]
                elif os.path.isfile(possible_root_path + '.py'):
                    possible_root_path = possible_root_path + '.py'
                    return [possible_root_path]
                current_search_dir = os.path.dirname(current_search_dir)
            return []


def find_all_dependencies(file_paths: list, project_root: str):
    dependencies = set()
    to_process = file_paths.copy()
    processed = set()

    while to_process:
        current_file = os.path.abspath(to_process.pop())
        if current_file in processed:
            continue

        processed.add(current_file)
        dependencies.add(current_file)

        try:
            imported_modules = find_imported_modules(current_file)
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error in file {current_file}: {e}")

        # potential_init_file = os.path.abspath(os.path.join(os.path.dirname(current_file), '__init__.py'))
        # if os.path.exists(potential_init_file) and potential_init_file not in processed:
        #     to_process.append(potential_init_file)
        #     dependencies.add(potential_init_file)

        for module in imported_modules:
            module_path = resolve_module_path(module, current_file, project_root)
            if len(module_path) > 0:
                for each_module_path in module_path:
                    each_module_path = os.path.abspath(each_module_path)
                    if each_module_path not in processed:
                        to_process.append(each_module_path)

    return dependencies


def enhance_import_for_py_files(addon_dir: str):
    namespace = os.path.basename(addon_dir)
    all_py_modules = find_all_py_modules(addon_dir)
    all_py_file = search_files(addon_dir, {".py"})
    for py_file in all_py_file:
        content = read_utf8(py_file)
        for module_path in _import_module_pattern.finditer(content):
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
    path = PROJECT_ROOT
    event_handler = FileUpdateHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
            if event_handler.has_update:
                try:
                    update_addon_for_test(init_file, addon_name)
                    event_handler.clear_update()
                except Exception as e:
                    print(e)
                    print(
                        "Addon updated failed: Please make sure no other process is"
                        " using the addon folder. You might need to restart the test to update the addon in Blender.")
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
    write_utf8(os.path.join(test_addon_path, _addon_md5__signature), addon_md5)
