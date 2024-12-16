from common.i18n.dictionary import preprocess_dictionary

dictionary = {
    "zh_CN": {
        ("*", "Example Addon Side Bar Panel"): "示例插件面板",
        ("*", "Example Functions"): "示例功能",
        ("*", "ExampleAddon"): "示例插件",
        ("*", "Resource Folder"): "资源文件夹",
        ("*", "Int Config"): "整数参数",
        # This is not a standard way to define a translation, but it is still supported with preprocess_dictionary.
        "Boolean Config": "布尔参数",
        "Second Panel": "第二面板",
        ("*", "Add-on Preferences View"): "插件设置面板",
        ("Operator", "ExampleOperator"): "示例操作",
    }
}

dictionary = preprocess_dictionary(dictionary)

dictionary["zh_HANS"] = dictionary["zh_CN"]
