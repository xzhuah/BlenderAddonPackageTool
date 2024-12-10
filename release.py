from framework import get_init_file_path, release_addon
from main import ACTIVE_ADDON, IS_EXTENSION

# 发布前请修改ACTIVE_ADDON参数

# The name of the addon to be released, this name is defined in the config.py of the addon as __addon_name__
# 插件的config.py文件中定义的插件名称 __addon_name__


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('addon', default=ACTIVE_ADDON, nargs='?', help='addon name')
    parser.add_argument('--is_extension', default=IS_EXTENSION, action='store_true', help='If true, package the addon '
                                                                                          'as extension, framework '
                                                                                          'will convert absolute '
                                                                                          'import to relative import '
                                                                                          'for you and will take care '
                                                                                          'of packaging the '
                                                                                          'extension. Default is the '
                                                                                          'value of IS_EXTENSION')
    parser.add_argument('--disable_zip', default=False, action='store_true', help='If true, release the addon into a '
                                                                                  'plain folder and do not zip it '
                                                                                  'into an installable package, '
                                                                                  'useful if you want to add more '
                                                                                  'files and zip by yourself.')
    parser.add_argument('--with_version', default=False, action='store_true', help='Append the addon version number ('
                                                                                   'as specified in bl_info) to the '
                                                                                   'released zip file name.')
    parser.add_argument('--with_timestamp', default=False, action='store_true', help='Append a timestamp to the zip '
                                                                                     'file name.')
    args = parser.parse_args()
    release_addon(target_init_file=get_init_file_path(args.addon),
                  addon_name=args.addon,
                  need_zip=not args.disable_zip,
                  is_extension=args.is_extension,
                  with_timestamp=args.with_timestamp,
                  with_version=args.with_version,
                  )
