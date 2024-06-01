# Blender Add-on Development Framework and Packaging Tool

This project provides a basic framework for developing Blender add-ons and a packaging tool. The main features include:

1. A single command to create a template add-on, facilitating quick development.
2. Integration with an IDE, allowing you to run and test your add-on in Blender with a single command. Support hot swap
   for code changes. You can see the changes in Blender immediately after saving the code.
3. A single command to package the add-on into an installable package, making it easier for users to install. The
   packaging tool automatically detects and includes any dependencies required by the add-on.
4. A framework supporting simultaneous development of multiple add-ons, enabling code reuse across different add-ons.
5. Handy development tools, like an auto-load utility for automatic class loading and an internationalization (i18n)
   tool, to assist even new developers in creating high-quality add-ons.

Install the following external library to use this project in an IDE:
https://github.com/nutti/fake-bpy-module
https://github.com/gorakhargosh/watchdog

## Basic Framework

- [main.py](main.py): Configures the Blender path, add-on installation path, default add-on, package ignore files, and
  add-on release path, among other settings.
- [test.py](test.py): A testing tool to run and test add-ons.
- [create.py](create.py): A tool to create add-ons, allowing you to quickly create an add-on based on the `sample_addon`
  template.
- [release.py](release.py): A packaging tool that packages add-ons into an installable package.
- [addons](addons): A directory to store add-ons, with each add-on in its own sub-directory. Use `create.py` to quickly
  create a new add-on.
- [common](common): A directory to store shared utilities.

## Framework Development Guidelines

Blender Version >= 2.93

Each add-on, while adhering to the basic structure of a Blender add-on, should include a `config.py` file to configure
the add-on's package name, ensuring it doesn't conflict with other add-ons.
When importing dependencies, always use the full package name, such
as `from addons.sample_addon.config import __addon_name__`.
Avoid relative imports, such as `from .config import __addon_name__`.

This project depends on the `addons` folder; do not rename this folder.

## Usage

1. Clone this repository.
1. Open this project in your IDE. Optional: Configure the IDE to use the same python interpreter as Blender.
1. Note: For PyCharm users, change the value idea.max.intellisense.filesize in idea.properties file ( Help | Edit Custom
   Properties.) to more than 2600 because some modules have the issue of being too big for intelliSense to work.
2. Configure the name of the addon you want to create (ACTIVE_ADDON) in [main.py](main.py).
1. Run create.py to create a new addon in your IDE
1. Develop your addon in the newly created addon directory.
1. Run test.py to test your addon in Blender.
1. Run release.py to package your addon into an installable package. The packaged addon path will appears in the
   terminal when packaged successfully.

# Features Provided by the Framework
1. You don't need to worry about register and unregister classes in Blender add-ons. The framework automatically loads and
   unloads classes in your add-ons. You just need to define your classes in the addon's folder.
2. You can use internationalization in your add-ons. Just add translations in the standard format to the `dictionary.py`
   file in the `i18n` folder of your add-on.
3. You can define RNA properties declaratively. Just follow the examples in the `__init__.py` file to add your RNA
   properties. The framework will automatically register and unregister your RNA properties.
4. You can use the `ExpandableUi` class in `common/types/framework.py` to easily extend Blender's native UI components,
   such as menus, panels, pie menus, and headers. Just inherit from this class and implement the `draw` method. You can
   specify the ID of the native UI component you want to extend using `target_id` and specify whether to append or
   prepend using `expand_mode`.


# Blender 插件开发框架及打包工具

本项目是一个基础的Blender插件开发框架和打包工具. 主要功能包括：

1. 一条命令创建一个模版插件插件，方便进行快速开发
2. 与IDE集成，在IDE中可以通过一条命令在Blender上运行插件的测试, 支持代码热更新，保存代码后可以立即在Blender中看到变化
3. 一条命令将插件打包成一个安装包，方便用户安装，打包工具自动检测插件的依赖关系，自动打包插件所需的依赖文件
4. 提供了一个支持多个插件同时开发的框架，方便插件开发者进行跨插件的功能复用
5. 提供了常用的插件开发工具，比如自动加载类的auto_load工具，提供国际化翻译的i18n工具，方便新手开发者进行高水平插件开发

请安装以下外部库以便在IDE中使用本项目：
https://github.com/nutti/fake-bpy-module
https://github.com/gorakhargosh/watchdog

## 基础框架

[main.py](main.py): 可以配置Blender路径，插件安装路径，当前默认插件，打包ignore文件，插件发布路径等

[test.py](test.py): 测试工具，可以运行插件的测试

[create.py](create.py): 创建插件的工具，可以根据sample_addon模版快速创建一个插件

[release.py](release.py): 打包工具，可以将插件打包成一个安装包

[addons](addons): 存放插件的目录，每个插件一个目录，使用create.py可以快速创建一个插件

[common](common): 存放公共工具的目录

## 框架开发要求

Blender 版本 >= 2.93

每个插件在符合Blender插件的结构基础上，需要有一个config.py文件用于配置插件的包名，避免与其他插件冲突。
在导入依赖时需要书写完整包名，比如 `from addons.sample_addon.config import __addon_name__`
避免使用相对路径导入，比如 `from .config import __addon_name__`

注意项目依赖addons文件夹，请勿更改这个文件夹的名称。

## 使用说明

1. 克隆此项目。
1. 在您的 IDE 中打开此项目。你可以将IDE使用的Python.exe配置成与Blender相同。
2. 对于PyCharm用户，请将idea.properties文件(点击 Help | Edit Custom Properties.)
   中的idea.max.intellisense.filesize的值更改为大于2600，因为某些模块的大小超过了intelliSense的工作范围。
1. 在 [main.py](main.py) 中配置 Blender 可执行文件路径（BLENDER_EXE_PATH）
1. 在 [main.py](main.py) 中配置您想要创建的插件名称（ACTIVE_ADDON）。
1. 运行 create.py 在您的 IDE 中创建一个新的插件。
1. 在新创建的插件目录中开发您的插件。
1. 运行 test.py 在 Blender 中测试您的插件。
1. 运行 release.py 将您的插件打包成可安装的包。成功打包后，终端中将显示打包插件的路径。

## 框架提供的功能

1. 你基本上无需关心Blender插件的类的加载和卸载，框架会自动加载和卸载你的插件中的类
2. 你可以在插件中使用国际化翻译，只需要在插件文件夹中的i18n中的dictionary.py文件中按标准格式添加翻译即可
3. 你可以使用声明式的方式定义RNA属性，只需要根据__init__.py中的注释示例添加你的RNA属性即可，框架会自动注册和卸载你的RNA属性
4.
你可以使用common/types/framework.py中的ExpandableUi类来方便的扩展Blender原生的菜单，面板，饼菜单，标题栏等UI组件,只需继承该类并实现draw方法，你可以通过target_id来指定需要扩展的原生UI组件的ID,
通过expand_mode来指定向前还是向后扩展。