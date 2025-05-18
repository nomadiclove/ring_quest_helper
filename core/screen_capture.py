import pyautogui
import numpy as np
import cv2 # 用于颜色空间转换 (RGB -> BGR)
import os

# 导入我们自己的模块 (注意相对路径，假设screen_capture.py在core目录下)
# from .window_manager import find_game_window, get_window_rect # 如果需要直接依赖WindowMananger获取窗口信息
# from .config_loader import load_config_file, get_config_value # 如果需要直接读取配置

def capture_screen_area(screen_x, screen_y, width, height):
    """
    截取屏幕上指定矩形区域的图像。

    参数:
    - screen_x (int): 截图区域左上角的屏幕X坐标。
    - screen_y (int): 截图区域左上角的屏幕Y坐标。
    - width (int): 截图区域的宽度。
    - height (int): 截图区域的高度。

    返回:
    - numpy.ndarray: BGR格式的图像数据。
    - None: 如果截图失败或参数无效。
    """
    if width <= 0 or height <= 0:
        # print("错误 (capture_screen_area): 截图宽度和高度必须大于0。") # 遵循原则，暂时不打印
        return None

    try:
        # pyautogui.screenshot() 返回一个 Pillow Image 对象 (RGB模式)
        screenshot_pil = pyautogui.screenshot(region=(screen_x, screen_y, width, height))

        # 将 Pillow Image 转换为 OpenCV BGR NumPy array
        screenshot_bgr = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
        return screenshot_bgr
    except Exception: # 捕获截图时可能发生的各种异常
        # print(f"错误 (capture_screen_area): 截图失败 - {e}") # 暂时不打印
        return None


def get_game_client_area_rect(window_manager_module, config_loader_module, general_config_filename="settings_general.ini"):
    """
    计算并返回游戏内部画面 (例如1366x768) 在屏幕上的绝对坐标和尺寸。
    这需要先找到游戏窗口，获取其外部矩形，然后根据配置的偏移量计算。

    参数:
    - window_manager_module: 已导入的 window_manager 模块。
    - config_loader_module: 已导入的 config_loader 模块。
    - general_config_filename (str): 包含游戏窗口和客户端区域偏移配置的文件名。

    返回:
    - tuple: (client_area_screen_x, client_area_screen_y, client_area_width, client_area_height)
    - None: 如果无法找到窗口或读取配置失败。
    """
    # 1. 加载通用配置
    general_config = config_loader_module.load_config_file(general_config_filename)
    if not general_config:
        return None

    # 2. 从配置中获取窗口查找参数和客户端区域偏移
    try:
        title_pattern = general_config.get('GameWindow', 'TitlePattern')
        expected_width = general_config.getint('GameWindow', 'ExpectedWidth')
        expected_height = general_config.getint('GameWindow', 'ExpectedHeight')

        offset_x = general_config.getint('ScreenCapture', 'ClientAreaOffsetX')
        offset_y = general_config.getint('ScreenCapture', 'ClientAreaOffsetY')
        client_width = general_config.getint('ScreenCapture', 'ClientAreaWidth')
        client_height = general_config.getint('ScreenCapture', 'ClientAreaHeight')
    except Exception: # 捕获 get 或 getint 可能的错误 (NoSection, NoOption, ValueError)
        # print(f"错误 (get_game_client_area_rect): 读取配置失败 - {e}") # 暂时不打印
        return None

    # 3. 查找游戏窗口
    game_window = window_manager_module.find_game_window(title_pattern, expected_width, expected_height)
    if not game_window:
        return None

    # 4. 获取窗口的外部屏幕矩形
    window_rect = window_manager_module.get_window_rect(game_window)
    if not window_rect:
        return None

    window_screen_x, window_screen_y, _, _ = window_rect

    # 5. 计算内部游戏客户端区域的屏幕绝对坐标
    client_area_screen_x = window_screen_x + offset_x
    client_area_screen_y = window_screen_y + offset_y

    return (client_area_screen_x, client_area_screen_y, client_width, client_height)