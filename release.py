from main import get_init_file_path, release_addon, ACTIVE_ADDON

# 发布前请修改以下参数

# The name of the addon to be released, this name is defined in the config.py of the addon as __addon_name__
# 插件的config.py文件中定义的插件名称 __addon_name__
addon_name_to_release = ACTIVE_ADDON
# addon_name_to_release = "new_addon"

if __name__ == '__main__':
    release_addon(get_init_file_path(addon_name_to_release), addon_name_to_release)
