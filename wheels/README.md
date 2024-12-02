# How to include Python wheels for addons starting from Blender 4.2

Please read https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html for context.

To bundle Python wheels with your addon, you need to download to this `wheels` directory.
And In blender_manifest.toml include the wheels as a list of paths, e.g.:

```
wheels = [
   "./wheels/pillow-10.3.0-cp311-cp311-macosx_11_0_arm64.whl",
   "./wheels/pillow-10.3.0-cp311-cp311-manylinux_2_28_x86_64.whl",
   "./wheels/pillow-10.3.0-cp311-cp311-win_amd64.whl",
]
```

When you release your addon, the framework will copy these wheels into the zip file according to the toml configuration.
This way you don't have to maintain wheels in your addon directory which could lead to duplication.

Noticed that when testing your addon, the framework will not automatically include these wheels to avoid
overhead. You might see `ModuleNotFoundError` when testing your addon even though you have included the wheels in the
project.
To solve that, you need to install them manually using `pip install` or `python -m pip install` for your testing
Blender python environment. This could also be done in the IDE if you choose to use the same python environment for
developing.

[]:

# 如何给Blender 4.2及以后的插件添加 Python wheels

请参考 https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html 了解背景知识。

给插件添加 Python wheels ,你需要将.whl文件下载到这个 `wheels` 文件夹中.
并且在插件配置文件 blender_manifest.toml 中声明插件所需的whl文件路径，例如:

```
wheels = [
   "./wheels/pillow-10.3.0-cp311-cp311-macosx_11_0_arm64.whl",
   "./wheels/pillow-10.3.0-cp311-cp311-manylinux_2_28_x86_64.whl",
   "./wheels/pillow-10.3.0-cp311-cp311-win_amd64.whl",
]
```

当你打包插件时，框架会根据toml将这些whl文件复制到zip文件中。因此你不需要在插件的目录中存放这些whl文件导致重复。

注意，当你测试插件时，框架不会自动包含这些whl文件以避免额外的开销。你可能会在测试插件时看到 `ModuleNotFoundError`
错误，即使你已经在项目中包含了这些whl文件。
为此你需要手动使用 `pip install` 或 `python -m pip install` 命令
将这些whl文件安装到你进行测试的Blender python环境中。如果你恰巧选择在IDE中使用相同的python环境进行开发，你也可以通过IDE中安装这些whl文件。

