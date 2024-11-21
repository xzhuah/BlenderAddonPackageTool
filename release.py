from main import get_init_file_path, release_addon, ACTIVE_ADDON

# 发布前请修改以下参数

# The name of the addon to be released, this name is defined in the config.py of the addon as __addon_name__
# 插件的config.py文件中定义的插件名称 __addon_name__
addon_name_to_release = ACTIVE_ADDON
# addon_name_to_release = "new_addon"

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('addon', default=ACTIVE_ADDON, nargs='?', help='addon name')
    parser.add_argument('--need_zip', default=True, action='store_true', help='need zip package')
    parser.add_argument('--with_version', default=False, action='store_true', help='append version')
    parser.add_argument('--with_timestamp', default=False, action='store_true', help='append timestamp')
    args = parser.parse_args()
    release_addon(target_init_file = get_init_file_path(args.addon), 
                  addon_name = addon_name_to_release,
                  need_zip= args.need_zip,
                  with_timestamp = args.with_timestamp,
                  with_version = args.with_version,
                )
