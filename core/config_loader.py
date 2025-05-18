import configparser
import os

_loaded_configs = {} # 缓存已加载的配置文件对象

def load_config_file(file_name, config_dir="config"):
    """
    加载指定的 .ini 配置文件。
    会缓存已加载的配置，避免重复读取。

    参数:
    - file_name (str): 配置文件的名称 (例如 "settings_ui_layout.ini")。
    - config_dir (str): 配置文件所在的目录路径 (相对于项目根目录)。

    返回:
    - configparser.ConfigParser: 加载的配置对象。
    - None: 如果文件未找到或加载失败。
    """
    global _loaded_configs

    # 构建到项目根目录的路径，然后到config目录
    # __file__ 是当前脚本 (config_loader.py) 的路径
    # os.path.dirname(__file__) 是 core 目录
    # os.path.dirname(os.path.dirname(__file__)) 是项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_file_path = os.path.join(project_root, config_dir, file_name)

    if config_file_path in _loaded_configs:
        return _loaded_configs[config_file_path]

    if not os.path.exists(config_file_path):
        # print(f"错误 (load_config_file): 配置文件未找到: {config_file_path}") # 遵循原则，暂时不打印
        return None

    config = configparser.ConfigParser()
    try:
        config.read(config_file_path, encoding='utf-8')
        _loaded_configs[config_file_path] = config
        return config
    except configparser.Error: # 捕获所有configparser相关的解析错误
        # print(f"错误 (load_config_file): 解析配置文件失败: {config_file_path}") # 暂时不打印
        return None


def get_section_dict(config_parser_object, section_name):
    """
    从已加载的 ConfigParser 对象中获取指定段落的所有键值对，作为字典返回。

    参数:
    - config_parser_object (configparser.ConfigParser): 已加载的配置对象。
    - section_name (str): 要获取的段落名称。

    返回:
    - dict: 包含该段落所有键值对的字典。
    - None: 如果配置对象无效或段落不存在。
    """
    if not config_parser_object or not isinstance(config_parser_object, configparser.ConfigParser):
        return None
    if not config_parser_object.has_section(section_name):
        # print(f"警告 (get_section_dict): 段落 '{section_name}' 在配置中未找到。") # 暂时不打印
        return None # 或者返回空字典 {}，取决于你希望如何处理

    return dict(config_parser_object.items(section_name))


def get_config_value(config_dict, key, default_value=None, value_type=str):
    """
    从配置字典中获取指定键的值，并进行可选的类型转换。

    参数:
    - config_dict (dict): 从 get_section_dict 获取的配置字典。
    - key (str): 要获取的键名 (不区分大小写，因为ConfigParser默认不区分)。
    - default_value (any, optional): 如果键不存在，返回的默认值。
    - value_type (type, optional): 期望的值类型 (例如 int, float, bool, str)。
                                   对于bool, "true", "yes", "on", "1" (不区分大小写) 会被转为True,
                                   "false", "no", "off", "0" 会被转为False。

    返回:
    - any: 获取到的值 (可能已转换类型)，或默认值。
    - None: 如果键不存在且未提供默认值，或类型转换失败。
    """
    if not config_dict or not isinstance(config_dict, dict):
        return default_value if default_value is not None else None

    # ConfigParser 默认会将键名转为小写
    value_str = config_dict.get(key.lower())

    if value_str is None:
        return default_value

    try:
        if value_type == bool:
            if value_str.lower() in ('true', 'yes', 'on', '1'):
                return True
            elif value_str.lower() in ('false', 'no', 'off', '0'):
                return False
            else: #无法转换为bool，可以返回默认值或None，或抛出异常
                return default_value # 或者 raise ValueError
        elif value_type == str:
            return value_str
        else: # int, float 等
            return value_type(value_str)
    except ValueError:
        # print(f"警告 (get_config_value): 值 '{value_str}' 无法转换为类型 {value_type.__name__} for key '{key}'.") # 暂时不打印
        return default_value if default_value is not None else None