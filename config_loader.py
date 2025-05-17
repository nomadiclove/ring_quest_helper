# 文件名: config_loader.py
# 位置: ring_quest_helper/config_loader.py

import configparser
import os
import json  # 导入json库

CONFIG_FILE = 'config.ini'
TASK_KEYWORDS_FILE = 'tasks_keywords.json'  # 定义JSON文件名
ITEM_KEYWORDS_FILE = 'item_keywords.json'     # <--- 新增
ITEM_SOURCING_RULES_FILE = 'item_sourcing_rules.json' # <--- 新增

def load_config():
    """加载主配置文件 (config.ini)"""
    config = configparser.ConfigParser()
    # 修正：确保config_loader.py和配置文件在同一目录或可访问
    # 通常config_loader.py和项目根目录的config.ini在同一级，或者config_loader.py能定位到它
    # 如果main.py在根目录，config_loader.py也在根目录，则os.path.dirname(__file__)是根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, CONFIG_FILE)

    if not os.path.exists(config_path):
        # 如果config_loader.py在子目录（比如core/），config.ini在上一级，路径可能需要调整
        # 例如: config_path = os.path.join(os.path.dirname(script_dir), CONFIG_FILE)
        # 但我们目前的结构是都放在根目录（或main.py能正确找到它们）
        raise FileNotFoundError(f"错误：配置文件 '{config_path}' 未找到。")

    config.read(config_path, encoding='utf-8')
    return config


def get_config_value(config, section, key, fallback=None):
    """从加载的config对象中获取特定值。"""
    try:
        return config.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        print(f"配置警告: 在配置节 '{section}' 中未找到键 '{key}'。将使用 fallback 值: {fallback}")
        return fallback


def load_task_keywords():
    """从JSON文件加载任务关键字映射。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    keywords_file_path = os.path.join(script_dir, TASK_KEYWORDS_FILE)  # 假设keywords文件与此脚本同级
    # 或根据实际情况调整路径
    try:
        with open(keywords_file_path, 'r', encoding='utf-8') as f:
            keywords_map = json.load(f)
        print(f"DEBUG: 已成功从 '{keywords_file_path}' 加载任务关键字。")
        return keywords_map
    except FileNotFoundError:
        print(f"错误：任务关键字文件 '{keywords_file_path}' 未找到。将返回空字典。")
        return {}
    except json.JSONDecodeError:
        print(f"错误：解析任务关键字文件 '{keywords_file_path}' 失败。请检查JSON格式。将返回空字典。")
        return {}
    except Exception as e:
        print(f"加载任务关键字文件时发生未知错误: {e}")
        return {}

def load_json_file(filename, error_message_prefix=""):
    """通用加载JSON文件的函数"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data_map = json.load(f)
        print(f"DEBUG: 已成功从 '{file_path}' 加载 {error_message_prefix}数据。")
        return data_map
    except FileNotFoundError:
        print(f"错误：{error_message_prefix}文件 '{file_path}' 未找到。将返回空字典。")
        return {}
    except json.JSONDecodeError:
        print(f"错误：解析{error_message_prefix}文件 '{file_path}' 失败。请检查JSON格式。将返回空字典。")
        return {}
    except Exception as e:
        print(f"加载{error_message_prefix}文件时发生未知错误: {e}")
        return {}

def load_item_keywords():
    """从JSON文件加载物品关键字映射。"""
    return load_json_file(ITEM_KEYWORDS_FILE, error_message_prefix="物品关键字")

def load_item_sourcing_rules():
    """从JSON文件加载物品获取规则。"""
    return load_json_file(ITEM_SOURCING_RULES_FILE, error_message_prefix="物品获取规则")


if __name__ == '__main__':
    # ... (原有的测试代码) ...
    print("\n测试加载物品关键字文件...")
    item_kw = load_item_keywords()
    if item_kw:
        print(f"  加载到的'天书残卷一'关键字: {item_kw.get('天书残卷一', '未找到该物品')}")
    else:
        print("  未能加载物品关键字。")

    print("\n测试加载物品获取规则文件...")
    sourcing_rules = load_item_sourcing_rules()
    if sourcing_rules:
        print(f"  '优先背包'列表中的物品数量: {len(sourcing_rules.get('优先背包', []))}")
        print(f"  '优先打造'列表中的物品数量: {len(sourcing_rules.get('优先打造', []))}")
    else:
        print("  未能加载物品获取规则。")
    print("\n配置文件加载器测试完毕。")
