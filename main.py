import pyautogui # 主要用于初始的 sleep
import cv2
import numpy as np
import os
import configparser # 用于加载主配置
import traceback

# 导入我们重构后的模块
from core.window_manager import find_game_window, activate_window, get_window_rect
from core.config_loader import load_config_file # 我们会用它加载多个配置文件
from core.screen_capture import capture_screen_area, get_game_client_area_rect
from core.input_simulator import click_screen_coords # 或者整个 input_simulator 模块
# tasks.jianduoshiguang_processor 会在下面按需导入

def run_automation():
    print("自动化脚本启动 (主调度器)...")

    # --- 0. 加载主配置文件和项目根目录 ---
    # 假设 main.py 在项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))

    # 加载通用配置，其中应包含其他配置文件的信息或窗口信息
    # 我们约定 settings_general.ini 是主入口配置
    general_config_path = os.path.join(project_root, "config", "settings_general.ini")
    if not os.path.exists(general_config_path):
        print(f"主配置文件未找到: {general_config_path}")
        return

    config = configparser.ConfigParser()
    try:
        config.read(general_config_path, encoding='utf-8')
        # 将项目根路径也存入配置，方便其他模块使用（如果它们需要读取相对于项目根的文件）
        if not config.has_section('Paths'):
            config.add_section('Paths')
        config.set('Paths', 'ProjectRoot', project_root)

        # (可选) 加载其他配置文件并合并到主config对象，或者按需加载
        # 例如，ui_layout_config_path = os.path.join(project_root, "config", config.get('ConfigFiles', 'UILayout', fallback='settings_ui_layout.ini'))
        # config.read(ui_layout_config_path, encoding='utf-8')
        # 为了简单，jianduoshiguang_processor 会自己加载它需要的特定配置部分，或者我们在这里一次性加载所有需要的ini文件到config对象
        # 我们先让 process_jianduoshiguang 自己处理其内部需要的配置读取，只需传入主 config 对象

    except Exception as e:
        print(f"加载主配置文件 '{general_config_path}' 失败: {e}")
        return

    # --- 1. 窗口处理 ---
    window_title = config.get('GameWindow', 'TitlePattern', fallback="大话西游2经典版")
    expected_w = config.getint('GameWindow', 'ExpectedWidth', fallback=1378)
    expected_h = config.getint('GameWindow', 'ExpectedHeight', fallback=831)

    game_window = find_game_window(window_title, expected_w, expected_h)
    if not game_window:
        print(f"未能找到标题为 '{window_title}' 且尺寸约为 {expected_w}x{expected_h} 的游戏窗口。")
        return

    activate_window(game_window)
    pyautogui.sleep(0.2) # 给窗口一点响应时间

    # --- 2. 获取游戏内部画面截图及其屏幕绝对矩形 ---
    # get_game_client_area_rect 需要 window_manager 和 config_loader 模块本身作为参数
    # 或者我们可以修改 get_game_client_area_rect 让它直接接收 config 对象和 window_object
    # 为了更符合你的“不要二次封装”原则，我们直接在这里执行计算

    window_abs_rect = get_window_rect(game_window)
    if not window_abs_rect:
        print("未能获取游戏窗口的屏幕矩形。")
        return

    client_offset_x = config.getint('ScreenCapture', 'ClientAreaOffsetX')
    client_offset_y = config.getint('ScreenCapture', 'ClientAreaOffsetY')
    client_width = config.getint('ScreenCapture', 'ClientAreaWidth')
    client_height = config.getint('ScreenCapture', 'ClientAreaHeight')

    game_client_abs_x = window_abs_rect[0] + client_offset_x
    game_client_abs_y = window_abs_rect[1] + client_offset_y
    game_client_abs_rect = (game_client_abs_x, game_client_abs_y, client_width, client_height)

    print(f"游戏内部画面在屏幕上的绝对矩形: {game_client_abs_rect}")

    main_game_image_bgr = capture_screen_area(game_client_abs_x, game_client_abs_y, client_width, client_height)
    if main_game_image_bgr is None:
        print("截取游戏内部画面失败。")
        return
    print("游戏内部画面已截图。")
    # cv2.imwrite("debug_main_game_screen.png", main_game_image_bgr) # DEBUG

    # --- 3. 任务识别与分发 (当前只处理见多识广) ---
    # 导入任务处理器 (由于tasks是jianduoshiguang_processor.py的父目录，需要正确处理导入)
    try:
        # 假设 tasks 目录与 main.py 在同一级或已在PYTHONPATH中
        # 或者更健壮的方式是：
        import sys
        sys.path.append(os.path.join(project_root, 'tasks')) # 将tasks目录加入sys.path
        from jianduoshiguang_processor import process_jianduoshiguang
    except ImportError as e:
        print(f"错误：无法导入任务处理器模块 - {e}")
        print("请确保 tasks/jianduoshiguang_processor.py 文件存在且路径正确。")
        return

    # TODO: 在这里应该有一个任务识别的步骤，来确定当前是什么任务类型
    # current_task_type = identify_task_from_ui(main_game_image_bgr, config) 
    # 暂时我们直接调用 "见多识广" 的处理器

    print("-" * 30)
    print("开始处理 '见多识广' 类型任务...")

    # input_simulator 模块可以直接导入并使用其函数，不需要实例化
    import core.input_simulator as input_sim 

    task_status = process_jianduoshiguang(
        main_game_image_bgr,
        game_client_abs_rect, # 传递1366x768区域在屏幕上的绝对x,y,w,h
        config,               # 传递已加载的主配置对象
        input_sim             # 传递input_simulator模块
    )

    print("-" * 30)
    print(f"'见多识广' 任务处理完成，状态: {task_status}")


if __name__ == '__main__':
    try:
        run_automation()
    except Exception as e:
        print(f"脚本顶层发生未处理异常: {e}")
        traceback.print_exc()
    finally:
        print("自动化脚本执行完毕。")