from framework import new_addon
from main import ACTIVE_ADDON

# 创建前请修改以下参数

# The name of the addon to be created, this name is defined in the config.py of the addon as __addon_name__
# 插件的config.py文件中定义的插件名称 __addon_name__

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('addon', default=ACTIVE_ADDON, nargs='?', help='addon name')
    args = parser.parse_args()
    new_addon(args.addon)
