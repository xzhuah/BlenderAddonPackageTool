from framework import test_addon
from main import ACTIVE_ADDON

# 测试前请修改ACTIVE_ADDON参数

# The name of the addon to be tested, this name is defined in the config.py of the addon as __addon_name__
# 插件的config.py文件中定义的插件名称 __addon_name__

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('addon', default=ACTIVE_ADDON, nargs='?', help='addon name')
    parser.add_argument('--disable_watch', default=False, action='store_true', help='Do not reload addon when file '
                                                                                    'changed')
    args = parser.parse_args()
    test_addon(args.addon, enable_watch=not args.disable_watch)
