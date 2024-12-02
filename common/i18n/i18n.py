import bpy

# Get the language code when addon start up
__language_code__ = bpy.context.preferences.view.language

from .dictionary import common_dictionary

__dictionary__ = common_dictionary


# Dictionary for translation: https://docs.blender.org/api/current/bpy.app.translations.html
# {
#     "en_US": {
#         ("*", code1): "translation1",
#         ("Operator", code2): "translation2",
#     },
#     "zh_CN": {
#         ("*", key): "翻译",
#         ("*, key2): "翻译2"
#     }
# }

# Set a new dictionary for translation
def set_dictionary(new_dictionary: dict[str, dict[tuple, str]]):
    global __dictionary__
    __dictionary__ = new_dictionary


# Load additional dictionary for translation
def load_dictionary(additional_dictionary: dict[str, dict[tuple, str]]):
    global __dictionary__
    for key in additional_dictionary:
        if key in __dictionary__:
            __dictionary__[key].update(additional_dictionary[key])
        else:
            __dictionary__[key] = {}
            __dictionary__[key].update(additional_dictionary[key])


# 在需要拼接字符串的地方使用i18n函数
def i18n(content: str) -> str:
    global __language_code__, __dictionary__
    __language_code__ = bpy.context.preferences.view.language
    if __language_code__ not in __dictionary__:
        return content
    tuple_contents = [("*", content), ("Operator", content)]
    for tuple_content in tuple_contents:
        if tuple_content in __dictionary__[__language_code__]:
            return __dictionary__[__language_code__][tuple_content]
    for key in __dictionary__[__language_code__]:
        if key[1] == content:
            return __dictionary__[__language_code__][key]
    return content
