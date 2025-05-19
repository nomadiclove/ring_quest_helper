import pyautogui
import cv2
import numpy as np
import os
import configparser
import sys

# 导入我们重构后的模块
from core.window_manager import find_game_window, activate_window, get_window_rect
from core.screen_capture import capture_screen_area
# image_matcher, color_filter, text_recognizer 会在任务处理器中导入
from core.input_simulator import click_screen_coords # 或整个模块

def run_automation():
    print("自动化脚本启动 (极致精简版 V2)...")

    project_root = os.path.dirname(os.path.abspath(__file__))
    config = configparser.ConfigParser()

    config_files_to_load = [
        "settings_general.ini",
        "settings_ui_layout.ini",
        "settings_ocr.ini",
        "task_keywords.ini"
    ]
    loaded_file_paths_for_config_read = [os.path.join(project_root, "config", fname) for fname in config_files_to_load]

    successfully_read_files = config.read(loaded_file_paths_for_config_read, encoding='utf-8')
    print(f"已加载配置文件: {', '.join([os.path.basename(f) for f in successfully_read_files]) if successfully_read_files else '无或读取失败'}")

    if not config.has_section('paths'):
        config.add_section('paths')
    config.set('paths', 'projectroot', project_root)

    window_title = config.get('gamewindow', 'titlepattern') 
    expected_w = config.getint('gamewindow', 'expectedwidth')
    expected_h = config.getint('gamewindow', 'expectedheight')

    game_window = find_game_window(window_title, expected_w, expected_h)
    if game_window is None: # 明确检查 None
        print(f"错误：未能找到标题为 '{window_title}' 的游戏窗口，脚本终止。")
        return

    activate_window(game_window) 
    pyautogui.sleep(0.2) 

    window_abs_rect = get_window_rect(game_window) 
    if window_abs_rect is None: # 明确检查 None
        print("错误：未能获取游戏窗口的屏幕矩形，脚本终止。")
        return

    client_offset_x = config.getint('screencapture', 'clientareaoffsetx') 
    client_offset_y = config.getint('screencapture', 'clientareaoffsety')
    client_width = config.getint('screencapture', 'clientareawidth')
    client_height = config.getint('screencapture', 'clientareaheight')

    game_client_abs_x = window_abs_rect[0] + client_offset_x
    game_client_abs_y = window_abs_rect[1] + client_offset_y
    game_client_abs_rect = (game_client_abs_x, game_client_abs_y, client_width, client_height)

    print(f"游戏内部画面在屏幕上的绝对矩形: {game_client_abs_rect}")

    main_game_image_bgr = capture_screen_area(game_client_abs_x, game_client_abs_y, client_width, client_height)
    if main_game_image_bgr is None:
        print("错误：截取游戏内部画面失败，脚本终止。")
        return
    print("游戏内部画面已截图。")
    # cv2.imwrite(os.path.join(project_root, "debug_main_game_screen.png"), main_game_image_bgr)

    tasks_dir = os.path.join(project_root, 'tasks')
    if tasks_dir not in sys.path:
        sys.path.append(tasks_dir)

    from jianduoshiguang_processor import process_jianduoshiguang 

    print("-" * 30)
    print("开始处理 '见多识广' 类型任务 (调用处理器)...")

    import core.input_simulator as input_sim 

    task_status = process_jianduoshiguang(
        main_game_image_bgr,
        game_client_abs_rect, 
        config,              
        input_sim            
    )

    print("-" * 30)
    print(f"'见多识广' 任务处理完成，状态: {task_status}")


if __name__ == '__main__':
    run_automation()
    print("自动化脚本执行完毕。")