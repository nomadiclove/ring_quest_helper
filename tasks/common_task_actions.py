# 文件名: common_task_actions.py
# 位置: ring_quest_helper/tasks/common_task_actions.py

from ..core.image_recognizer import find_image_on_screen  # 注意相对导入
from ..core.input_controller import click_at  # 假设你input_controller里会有这个
import pyautogui
import time
import os


def open_backpack(config, assets_base_path):
    """尝试打开背包"""
    print("尝试打开背包...")
    backpack_button_img = get_config_value(config, 'UI_Buttons', 'BackpackOpenButton')  # 假设配置中有这个
    if not backpack_button_img:
        print("错误：背包打开按钮图片未在config.ini中配置。")
        return False

    button_path = os.path.join(assets_base_path, backpack_button_img)
    location = find_image_on_screen(button_path, confidence=0.8)  # 使用配置的或默认的置信度
    if location:
        pyautogui.click(location)
        print("已点击背包按钮。")
        # 此处应加入等待背包界面出现的逻辑，并返回是否成功打开
        time.sleep(1)  # 简单延时
        # success = wait_for_image(backpack_ui_feature_img, timeout=5) # 伪代码
        # return success
        return True  # 暂时返回True
    else:
        print("未找到背包打开按钮。")
        return False


def find_item_in_backpack(item_template_path, backpack_roi, num_pages_to_check=5):
    """
    在背包的指定ROI内查找物品模板，可翻页。
    :param item_template_path: 物品模板图片的完整路径。
    :param backpack_roi: 背包主要物品区域的 (x, y, w, h) 元组。
    :param num_pages_to_check: 最多检查多少页。
    :return: 找到物品则返回其在屏幕上的中心坐标，否则返回None。
    """
    print(f"在背包区域 {backpack_roi} 中查找物品 {item_template_path}...")
    for page in range(num_pages_to_check):
        location = find_image_on_screen(item_template_path, confidence=0.8, region=backpack_roi)  # 置信度可调
        if location:
            print(f"在背包第 {page + 1} 页找到物品。")
            return location

        # 如果没找到，尝试翻页 (假设有翻页按钮，或配置了翻页操作)
        # click_backpack_next_page_button() # 伪代码
        print(f"在背包第 {page + 1} 页未找到，尝试翻页 (如果实现了翻页逻辑)...")
        if page < num_pages_to_check - 1:  # 不是最后一页才延时
            time.sleep(0.7)  # 等待翻页动画
        if num_pages_to_check == 1:  # 如果只检查一页，这里就不打印了
            break

    print(f"检查完 {num_pages_to_check} 页后，在背包中未找到物品 {item_template_path}。")
    return None

# 其他通用函数，例如：
# close_backpack()
# click_dialog_option(option_template_path, dialog_roi)
# wait_for_ui_element(element_template_path, timeout, region=None)