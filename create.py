from main import new_addon, ACTIVE_ADDON

# 创建前请修改以下参数

# The name of the addon to be created, this name is defined in the config.py of the addon as __addon_name__
# 插件的config.py文件中定义的插件名称 __addon_name__
addon_name_to_create = ACTIVE_ADDON
# addon_name_to_create = "new_addon"

if __name__ == '__main__':
    new_addon(addon_name_to_create)
