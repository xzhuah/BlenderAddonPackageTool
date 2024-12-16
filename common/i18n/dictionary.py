common_dictionary = {
    "zh_CN": {
        # ("*", "translation"): "翻译",
    }
}

common_dictionary["zh_HANS"] = common_dictionary["zh_CN"]


# preprocess dictionary
def preprocess_dictionary(dictionary):
    for key in dictionary:
        invalid_items = {}
        for translate_key in dictionary[key]:
            if isinstance(translate_key, str):
                invalid_items[translate_key] = dictionary[key][translate_key]
        for invalid_item in invalid_items:
            translation = invalid_items[invalid_item]
            dictionary[key][("*", invalid_item)] = translation
            dictionary[key][("Operator", invalid_item)] = translation
            del dictionary[key][invalid_item]
    return dictionary
