
# 文件名: task_急人所急.py
# 位置: ring_quest_helper/tasks/task_急人所急.py

import re
import time
import pyautogui
import numpy as np

# 【重要修改】从新的、正确的模块导入
from core.opencv_utils import find_green_underlined_link_opencv # <--- 确保从这里导入
# 如果你在这个文件中还需要OCR功能:
# from core.ocr_utils import ocr_image_region
# 如果你在这个文件中还需要基础图像查找(比如找按钮模板):
# from core.image_utils import find_image
# from core.input_simulator import click_at # 等等

# ... (def extract_item_name_from_description 函数定义) ...
# ... (def handle_jirensuoji 函数定义，它内部会调用 find_green_underlined_link_opencv) ...
def extract_item_name_from_description(ocr_item_description_line, item_keywords_map):
    """
    从OCR识别的任务描述的特定行中提取标准化的物品名称。
    主要依赖 "快去找到一个XXXX,并将其交给YYYYY" 这种固定格式。

    :param ocr_item_description_line: OCR识别出的、期望包含物品名的那一行或几行任务描述文本。
    :param item_keywords_map: 物品名称关键字及其标准名的映射字典
                              (e.g., {"天书残卷一": ["天书残卷一", "天书一"]})
    :return: 第一个匹配到的标准化的物品名称字符串，或 None。
    """
    print(f"DEBUG (extract_item): 接收到的用于提取物品的描述文本: '{ocr_item_description_line}'")

    # 基础清理，主要去除可能干扰正则的空白和特定标签
    clean_desc_for_regex = ocr_item_description_line.replace('\n', '').replace(' ', '')
    clean_desc_for_regex = clean_desc_for_regex.replace('“', '').replace('”', '').replace('"', '')
    # 移除 "[江湖历练任务]" 或 "[江湖历练企务]" 等，如果它们可能出现在物品描述行
    clean_desc_for_regex = re.sub(r"\[江湖历练[任务务]+\]", "", clean_desc_for_regex)

    print(f"DEBUG (extract_item): 清理后用于正则提取的描述: '{clean_desc_for_regex}'")

    # 正则表达式尝试捕获 "快去找到一个" 或 "找到一个" 之后，到第一个逗号、中文逗号、左圆括号或 "并将其交给" 之前的内容
    # (?:...) 是非捕获组
    # ([^,，（(并]+) 是捕获组1，匹配一个或多个非指定分隔符的字符
    match = re.search(r"(?:快去找到一个|找到一个)([^,，（(并]+)", clean_desc_for_regex)

    extracted_raw_item_name = None
    if match and match.group(1):
        extracted_raw_item_name = match.group(1).strip()
        print(f"DEBUG (extract_item): 正则表达式初步提取的物品名: '{extracted_raw_item_name}'")
    else:
        print(f"DEBUG (extract_item): 正则表达式未能从描述中提取出物品名片段。")
        # 如果正则失败，我们仍然可以尝试用旧的关键字遍历方法，但作用于整个 ocr_item_description_line
        # （这部分作为后备，但理想情况是正则能工作）
        # 暂时，如果正则失败，我们就认为提取失败
        return None

    # 使用 item_keywords_map 来标准化这个提取出的名字
    # 构建一个包含所有关键字及其对应标准名的列表，并按关键字长度降序排列
    all_keywords_with_standard_name = []
    if item_keywords_map:  # 确保 item_keywords_map 不是 None 或空
        for standard_name, aliases in item_keywords_map.items():
            # 标准名自身也是关键字 (去除括号内容以便更通用匹配)
            clean_standard_name_for_match = re.sub(r"\(.*\)", "", standard_name).strip()
            all_keywords_with_standard_name.append((clean_standard_name_for_match, standard_name))
            if clean_standard_name_for_match != standard_name:
                all_keywords_with_standard_name.append((standard_name, standard_name))  # 也加入原始标准名

            for alias in aliases:
                clean_alias_for_match = re.sub(r"\(.*\)", "", alias).strip()
                all_keywords_with_standard_name.append((clean_alias_for_match, standard_name))
                if clean_alias_for_match != alias:
                    all_keywords_with_standard_name.append((alias, standard_name))

    # 去重并按关键字（用于匹配的部分）长度降序排列
    unique_keywords = []
    seen_match_keywords = set()
    for kw_match, std_name_return in all_keywords_with_standard_name:
        if kw_match not in seen_match_keywords and kw_match:  # 确保关键字非空
            unique_keywords.append((kw_match, std_name_return))
            seen_match_keywords.add(kw_match)
    sorted_keywords_for_matching = sorted(unique_keywords, key=lambda x: len(x[0]), reverse=True)

    # 现在用排序后的关键字列表去匹配正则提取出的 extracted_raw_item_name
    for keyword_to_match, actual_standard_item_name in sorted_keywords_for_matching:
        if keyword_to_match in extracted_raw_item_name:  # 在正则提取出的部分查找关键字
            print(
                f"DEBUG (extract_item): 通过关键字 '{keyword_to_match}' 匹配到标准物品名: '{actual_standard_item_name}'")

            # 特殊处理“天书残卷”系列 (如果需要从 "天书残卷五,七.八或九" 中选一个)
            if "天书残卷" in actual_standard_item_name:
                # extracted_raw_item_name 可能包含 "五,七.八或九"
                # 我们需要决定返回哪一个。根据你的描述“只要这4种都可以 给一本就行”，
                # 我们可以尝试找到第一个在 item_keywords_map 中定义的具体天书编号。

                # 先看正则提取出的部分是否直接就是一个带编号的完整天书名的一部分
                # (例如 extracted_raw_item_name 是 "天书残卷五" 或 "天书残卷九")
                # 这里的 actual_standard_item_name 已经是通过关键字匹配到的，它可能已经是带编号的了。

                # 如果任务描述是 "天书残卷五,七.八或九"
                # 且 item_keywords_map 中有 "天书残卷五" -> ["天书残卷五", "天书五"]
                # 且 item_keywords_map 中有 "天书残卷七" -> ["天书残卷七", "天书七"] 等
                # 那么，当正则提取出 "天书残卷五,七.八或九" 时，
                # 上面的关键字匹配可能会先匹配到 "天书残卷九" (如果 "九" 在 "五" 前面被检查)
                # 或者如果 "天书残卷" 是一个关键字，它会匹配到通用的天书名。

                # 简化逻辑：如果匹配到的 actual_standard_item_name 已经是带特定编号的天书，就直接用它。
                # 如果它是一个通用的 "天书残卷" (而你需要一个具体的)，则尝试从 extracted_raw_item_name 中找第一个数字。
                if actual_standard_item_name == "天书残卷" or "天书" == actual_standard_item_name:  # 假设你有一个通用的天书关键字
                    num_map = {"一": "一", "二": "二", "三": "三", "四": "四", "五": "五",
                               "六": "六", "七": "七", "八": "八", "九": "九", "十": "十"}
                    for num_str_cn, _ in num_map.items():
                        # 检查正则提取出的原始物品名部分是否包含这个中文数字
                        if num_str_cn in extracted_raw_item_name:
                            specific_天书_name = f"天书残卷{num_str_cn}"
                            # 检查这个精确的带编号天书是否在我们的item_keywords_map的标准名列表中
                            if specific_天书_name in item_keywords_map:
                                print(f"DEBUG (extract_item): 天书类，精确匹配到特定编号: {specific_天书_name}")
                                return specific_天书_name
                    print(f"DEBUG (extract_item): 天书类，未找到特定编号，返回通用匹配: '{actual_standard_item_name}'")
                    return actual_standard_item_name  # 返回通用匹配到的天书名

            return actual_standard_item_name  # 非天书，或已是特定天书

    print(
        f"DEBUG (extract_item): 正则提取名 '{extracted_raw_item_name}' 未能在item_keywords_map中标准化，或正则未提取到。")
    return None


def handle_jirensuoji(script_vars):
    """
    处理“急人所急”任务的核心逻辑。
    """
    print("INFO: 开始处理“急人所急”任务...")

    full_content_roi_pil_image = script_vars['full_content_roi_pil_image']
    task_tracker_content_roi_tuple = script_vars['task_tracker_content_roi_tuple']
    item_keywords_map = script_vars['item_keywords_map']
    ocr_full_description_text = script_vars['ocr_full_description_text']
    lower_green = script_vars['lower_green']
    upper_green = script_vars['upper_green']

    # 1. 从OCR描述中提取所需物品名称
    #    我们现在传递的是完整的OCR描述，extract_item_name_from_description内部会尝试解析
    required_item_name = extract_item_name_from_description(ocr_full_description_text, item_keywords_map)

    if not required_item_name:
        print("错误（急人所急）：未能从任务描述中识别出所需物品。任务处理失败。")
        return False

    print(f"任务需求物品 (标准化后): {required_item_name}")

    # 2. 查找并点击NPC链接
    print("INFO (急人所急): 查找NPC链接...")
    link_center_in_roi = find_green_underlined_link_opencv(
        full_content_roi_pil_image,
        lower_green,
        upper_green,
        assets_base_path=script_vars['assets_base_path'],  # 传递 assets_base_path
        loop_num=script_vars.get('loop_count', 0)  # 传递 loop_count
    )

    if not link_center_in_roi:
        print("错误（急人所急）：未能找到NPC链接。任务处理失败。")
        return False

    roi_origin_x, roi_origin_y = task_tracker_content_roi_tuple[0], task_tracker_content_roi_tuple[1]
    screen_click_x = roi_origin_x + link_center_in_roi[0]
    screen_click_y = roi_origin_y + link_center_in_roi[1]

    print(f"找到NPC链接，准备点击屏幕坐标: ({screen_click_x}, {screen_click_y})")
    pyautogui.click(screen_click_x, screen_click_y)
    print(f"已点击NPC链接，角色前往目标NPC '{ocr_full_description_text}' 中描述的NPC...")  # 尝试打印NPC信息

    # 【重要】后续步骤：检查背包、给予/打造逻辑将在这里实现
    # For now, we assume navigation has started.
    print("（急人所急）NPC链接已点击，后续给予/打造逻辑待实现。暂时认为此步骤完成。")
    return True