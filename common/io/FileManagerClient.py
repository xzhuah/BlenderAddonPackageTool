import hashlib
import os
from os import listdir


def get_all_filename(folder_path: str) -> list:
    if os.path.exists(folder_path):
        return [f for f in listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    else:
        return []


def get_all_subfolder(folder_path: str) -> list:
    return [f for f in listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]


# return true if path_a is a subdirectory under path_b
def is_subdirectory(path_a, path_b) -> bool:
    path_a = os.path.abspath(path_a)
    path_b = os.path.abspath(path_b)
    return os.path.commonpath([path_b]) == os.path.commonpath([path_a, path_b])


def is_filename_postfix_in(filename: str, target_set: set):
    if target_set is None or len(target_set) == 0:
        return True
    for postfix in target_set:
        if filename.lower().endswith(postfix.lower()):
            return True
    return False


# 搜索文件夹下所有文件 post_filter为后缀名集合 全小写
def search_files(folder_path: str, post_filter: set) -> list:
    def __depth_first_search_files_helper__(current_folder: str, pre_result: list):
        for filename in get_all_filename(current_folder):
            if is_filename_postfix_in(filename, post_filter):
                pre_result.append(os.path.join(current_folder, filename))
        all_folders = get_all_subfolder(current_folder)
        for folder in all_folders:
            __depth_first_search_files_helper__(os.path.join(current_folder, folder), pre_result)

    all_file = []
    __depth_first_search_files_helper__(folder_path, all_file)
    return all_file


def get_md5(filename):
    return hashlib.md5(open(filename, 'rb').read()).hexdigest()


def get_md5_folder(folder_path: str) -> str:
    all_files = search_files(folder_path, set())
    md5_content = ""
    for file in all_files:
        md5_content += get_md5(file)
    return hashlib.md5(md5_content.encode("utf-8")).hexdigest()


def read_utf8(filepath: str) -> str:
    with open(filepath, mode="r", encoding="utf-8") as f:
        return f.read()


def read_utf8_in_lines(filepath: str) -> list[str]:
    with open(filepath, mode="r", encoding="utf-8") as f:
        return f.readlines()


def write_utf8(filepath: str, content: str):
    with open(filepath, encoding="utf-8", mode="w") as f:
        f.write(content)


def write_utf8_in_lines(filepath: str, content: list[str]):
    with open(filepath, encoding="utf-8", mode="w") as f:
        f.writelines(content)
