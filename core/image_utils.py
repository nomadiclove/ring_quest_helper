# 文件名: image_utils.py
# 位置: ring_quest_helper/core/image_utils.py

import pyautogui
import os
from PIL import Image  # Pillow用于获取图片尺寸等


def find_image(image_path, confidence=0.8, region=None, grayscale=False):
    """
    在屏幕上（或指定区域内）定位给定的图片。
    返回图片中心点坐标 (x, y) 或 None。
    """
    if not os.path.exists(image_path):
        print(f"错误 (ImageUtils): 图片文件未找到 '{image_path}'")
        return None
    try:
        location = pyautogui.locateCenterOnScreen(
            image_path,
            confidence=confidence,
            region=region,
            grayscale=grayscale
        )
        return location
    except Exception as e:
        # PyAutoGUI 在找不到时，且confidence<1.0时，通常返回None而不是抛出ImageNotFoundException
        # 但其他错误可能发生，比如屏幕访问问题或OpenCV/Pillow问题
        print(f"错误 (ImageUtils): 在查找图片 '{image_path}' 时发生: {e}")
        return None


def find_all_images(image_path, confidence=0.8, region=None, grayscale=False):
    """
    在屏幕上（或指定区域内）定位所有匹配的图片。
    返回一个生成器，包含所有找到的图片区域的 (left, top, width, height) Box对象。
    """
    if not os.path.exists(image_path):
        print(f"错误 (ImageUtils): 图片文件未找到 '{image_path}'")
        return []  # 返回空列表或迭代器
    try:
        locations = pyautogui.locateAllOnScreen(
            image_path,
            confidence=confidence,
            region=region,
            grayscale=grayscale
        )
        return list(locations)  # 转为列表方便使用，尽管它是生成器
    except Exception as e:
        print(f"错误 (ImageUtils): 在查找所有图片 '{image_path}' 时发生: {e}")
        return []


def take_screenshot(region=None, save_path=None):
    """
    截取屏幕指定区域的图像。
    :param region: 元组 (left, top, width, height) 指定截图区域，如果为None则全屏。
    :param save_path: 图片保存路径（包含文件名），如果为None则不保存，直接返回Pillow Image对象。
    :return: Pillow Image 对象，如果截图失败则返回 None。
    """
    try:
        screenshot_pil = pyautogui.screenshot(region=region)
        if screenshot_pil and save_path:
            try:
                # 确保保存路径的目录存在
                save_dir = os.path.dirname(save_path)
                if save_dir and not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
                screenshot_pil.save(save_path)
                print(f"DEBUG (ImageUtils): 截图已保存到 '{save_path}'")
            except Exception as e_save:
                print(f"错误 (ImageUtils): 保存截图到 '{save_path}' 时失败: {e_save}")
        return screenshot_pil
    except Exception as e:
        print(f"错误 (ImageUtils): 截图时发生: {e}")
        return None


def get_image_dimensions(image_path):
    """获取图片的宽度和高度"""
    if not os.path.exists(image_path):
        print(f"错误 (ImageUtils): 图片文件未找到 '{image_path}' 无法获取尺寸。")
        return None
    try:
        with Image.open(image_path) as img:
            return img.size  # 返回 (width, height)
    except Exception as e:
        print(f"错误 (ImageUtils): 打开图片 '{image_path}' 获取尺寸时失败: {e}")
        return None


if __name__ == '__main__':
    print("测试 image_utils.py...")
    # 这里的测试需要你有实际的图片和屏幕环境
    # 例如，创建一个 test_assets 文件夹和里面的图片
    # test_img_path = "path/to/your/test_image.png"
    # if os.path.exists(test_img_path):
    #     loc = find_image(test_img_path, confidence=0.9)
    #     if loc:
    #         print(f"测试图片找到于: {loc}")
    #     else:
    #         print("测试图片未找到。")
    # else:
    #     print(f"测试图片 {test_img_path} 不存在。")

    # ss = take_screenshot(save_path="assets/test_screenshot.png")
    # if ss:
    #     print("全屏截图已保存到 assets/test_screenshot.png (如果assets目录存在)")
    print("image_utils.py 模块可被导入。")