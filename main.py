# BlenderAddonPackageTool - A framework for developing multiple blender addons in a single workspace
# Copyright (C) 2024 Xinyu Zhu

import os
from configparser import ConfigParser

from common.class_loader.module_installer import default_blender_addon_path, normalize_blender_path_by_system

# The name of current active addon to be created, tested or released
# 要创建、测试或发布的当前活动插件的名称
ACTIVE_ADDON = "sample_addon"

# The path of the blender executable. Blender2.93 is the minimum version required
# Blender可执行文件的路径，Blender2.93是所需的最低版本
BLENDER_EXE_PATH = "C:/software/general/Blender/blender-3.6.0-windows-x64/blender.exe"

# Linux example Linux示例
# BLENDER_EXE_PATH = "/usr/local/blender/blender-3.6.0-linux-x64/blender"

# MacOS examplenotice "/Contents/MacOS/Blender" will be appended automatically if you didn't write it explicitly
# MacOS示例 框架会自动附加"/Contents/MacOS/Blender" 所以您不必写出
# BLENDER_EXE_PATH = "/Applications/Blender/blender-3.6.0-macOS/Blender.app"

# Are you developing an extension(for Blender4.2) instead of legacy addon?
# https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html
# The framework will convert absolute import to relative import when packaging the extension.
# Make sure to update __addon_name__ in config.py if you are migrating from legacy addon to extension.
# 是否是面向Blender4.2以后的扩展而不是传统插件？
# https://docs.blender.org/manual/en/latest/advanced/extensions/addons.html
# 在打包扩展时，框架会将绝对导入转换为相对导入。如果你从传统插件迁移到扩展，请确保更新config.py中的__addon_name__
IS_EXTENSION = False

# You can override the default path by setting the path manually
# 您可以通过手动设置路径来覆盖默认插件安装路径 或者在config.ini中设置
# BLENDER_ADDON_PATH = "C:/software/general/Blender/Blender3.5/3.5/scripts/addons/"
BLENDER_ADDON_PATH = None
if os.path.exists(BLENDER_EXE_PATH):
    BLENDER_ADDON_PATH = default_blender_addon_path(BLENDER_EXE_PATH)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# 若存在config.ini则从其中中读取配置
CONFIG_FILEPATH = os.path.join(PROJECT_ROOT, 'config.ini')

# The default release dir. Must not within the current workspace
# 插件发布的默认目录，不能在当前工作空间内
DEFAULT_RELEASE_DIR = os.path.join(PROJECT_ROOT, "../addon_release/")

# The default test release dir. Must not within the current workspace
# 测试插件发布的默认目录，不能在当前工作空间内
TEST_RELEASE_DIR = os.path.join(PROJECT_ROOT, "../addon_test/")

if os.path.isfile(CONFIG_FILEPATH):
    configParser = ConfigParser()
    configParser.read(CONFIG_FILEPATH, encoding='utf-8')

    if configParser.has_option('blender', 'exe_path'):
        BLENDER_EXE_PATH = configParser.get('blender', 'exe_path')
        # The path of the blender addon folder
        # 同时更改Blender插件文件夹的路径
        BLENDER_ADDON_PATH = default_blender_addon_path(BLENDER_EXE_PATH)

    if configParser.has_option('blender', 'addon_path') and configParser.get('blender', 'addon_path'):
        BLENDER_ADDON_PATH = configParser.get('blender', 'addon_path')

    if configParser.has_option('default', 'addon') and configParser.get('default', 'addon'):
        ACTIVE_ADDON = configParser.get('default', 'addon')

    if configParser.has_option('default', 'is_extension') and configParser.get('default', 'is_extension'):
        IS_EXTENSION = configParser.getboolean('default', 'is_extension')

    if configParser.has_option('default', 'release_dir') and configParser.get('default', 'release_dir'):
        DEFAULT_RELEASE_DIR = configParser.get('default', 'release_dir')

    if configParser.has_option('default', 'test_release_dir') and configParser.get('default', 'test_release_dir'):
        TEST_RELEASE_DIR = configParser.get('default', 'test_release_dir')

BLENDER_EXE_PATH = normalize_blender_path_by_system(BLENDER_EXE_PATH)

# If you want to override theBLENDER_ADDON_PATH(the path to install addon during testing), uncomment the following line and set the path manually.
# 如果要覆盖BLENDER_ADDON_PATH(测试插件安装路径)，请取消下一行的注释并手动设置路径
# BLENDER_ADDON_PATH = ""

# Could not find the blender addon path, raise error. Please set BLENDER_ADDON_PATH manually.
# 未找到Blender插件路径，引发错误 请手动设置BLENDER_ADDON_PATH
if os.path.exists(BLENDER_EXE_PATH) and (not BLENDER_ADDON_PATH or not os.path.exists(BLENDER_ADDON_PATH)):
    raise ValueError("Blender addon path not found: " + BLENDER_ADDON_PATH, "Please set the correct path in config.ini")
