# 文件名: window_handler.py
# 位置: ring_quest_helper/core/window_handler.py

import pygetwindow as gw
import pyautogui  # 用于窗口激活失败时的备用点击
import time


def find_and_setup_game_window(window_title_from_config):
    """
    查找指定标题的游戏窗口，尝试激活它，并计算核心游戏区域的屏幕坐标。

    :param window_title_from_config: 从配置文件读取的游戏窗口的准确标题。
    :return: 如果成功找到并计算出核心游戏区，则返回一个元组 (x, y, width, height)
             代表核心游戏区域的屏幕绝对坐标和尺寸；否则返回 None。
    """
    print(f"DEBUG (WindowHandler): 正在查找标题为 '{window_title_from_config}' 的游戏窗口...")
    game_windows = gw.getWindowsWithTitle(window_title_from_config)

    if not game_windows:
        print(f"错误 (WindowHandler): 未找到标题为 '{window_title_from_config}' 的游戏窗口。")
        return None

    game_window = game_windows[0]  # 假设标题唯一，取第一个

    # 尝试恢复并激活窗口
    if game_window.isMinimized:
        print("DEBUG (WindowHandler): 游戏窗口已最小化，尝试恢复...")
        try:
            game_window.restore()
            time.sleep(0.7)  # 等待窗口恢复动画
        except Exception as e_restore:
            print(f"DEBUG (WindowHandler): 恢复窗口时出错: {e_restore}")

    if not game_window.isActive:
        print("DEBUG (WindowHandler): 游戏窗口非激活状态，尝试激活...")
        current_retries = 0
        max_activate_retries = 3
        activated = False
        while not activated and current_retries < max_activate_retries:
            current_retries += 1
            try:
                game_window.activate()
                time.sleep(0.7)  # 等待激活生效
                if game_window.isActive:
                    activated = True
                    print("DEBUG (WindowHandler): 游戏窗口已通过 activate() 激活。")
                    break
            except Exception as e_activate:
                print(f"DEBUG (WindowHandler): activate() 尝试 {current_retries} 失败: {e_activate}")

            if not activated and game_window.visible:  # 如果activate失败但窗口可见，尝试点击
                try:
                    print(
                        f"DEBUG (WindowHandler): activate() 失败，尝试通过点击窗口中心激活 (尝试 {current_retries})...")
                    pyautogui.click(game_window.centerx, game_window.centery)  # 点击窗口中心
                    time.sleep(0.7)
                    if game_window.isActive:  # 再次检查
                        activated = True
                        print("DEBUG (WindowHandler): 游戏窗口已通过点击激活。")
                        # break
                except Exception as e_click_activate:
                    print(f"DEBUG (WindowHandler): 点击窗口激活尝试 {current_retries} 失败: {e_click_activate}")
            time.sleep(0.5)  # 每次尝试后稍作等待

        if not activated:
            print(
                "警告 (WindowHandler): 多次尝试后游戏窗口仍未能激活，请手动将其置于前台。脚本将继续，但后续操作可能受影响。")
            # 即使没激活，也继续尝试获取坐标，因为后续PyAutoGUI的操作可能依然能作用于非活动窗口（取决于系统）
    else:
        print("DEBUG (WindowHandler): 游戏窗口已经是激活状态。")

    # 重新获取窗口几何信息，以防恢复/激活操作改变了它们
    parent_X = game_window.left
    parent_Y = game_window.top
    parent_W = game_window.width
    parent_H = game_window.height
    print(f"DEBUG (WindowHandler): 找到的父窗口屏幕坐标: 左={parent_X}, 上={parent_Y}, 宽={parent_W}, 高={parent_H}")

    # 根据你提供的详细描述计算核心游戏画面区域 (1366x768) 的屏幕绝对坐标
    gap_top_parent_to_subtitle = 28
    subtitle_height = 23
    gray_border_thickness = 6

    core_game_area_X_abs = parent_X + gray_border_thickness
    core_game_area_Y_abs = parent_Y + gap_top_parent_to_subtitle + subtitle_height + gray_border_thickness
    core_game_area_width = 1366  # 固定的核心游戏画面宽度
    core_game_area_height = 768  # 固定的核心游戏画面高度

    # 检查计算出的核心游戏区是否合理（例如，不能超出父窗口太多）
    if core_game_area_X_abs < parent_X or \
            core_game_area_Y_abs < parent_Y or \
            core_game_area_X_abs + core_game_area_width > parent_X + parent_W + 20 or \
            core_game_area_Y_abs + core_game_area_height > parent_Y + parent_H + 20:  # 允许一点点误差
        print(
            f"警告 (WindowHandler): 计算出的核心游戏区域 {core_game_area_X_abs, core_game_area_Y_abs, core_game_area_width, core_game_area_height} "
            f"与父窗口 {parent_X, parent_Y, parent_W, parent_H} 关系似乎不合理。请检查窗口结构描述和尺寸。")
        # 出现这种情况，可以考虑返回None或者整个父窗口区域作为备用
        # return (parent_X, parent_Y, parent_W, parent_H) # 或者None

    game_screen_region = (
        int(core_game_area_X_abs),
        int(core_game_area_Y_abs),
        int(core_game_area_width),
        int(core_game_area_height)
    )
    print(f"DEBUG (WindowHandler): 计算得到的核心游戏画面区域 (用于后续搜索): {game_screen_region}")
    return game_screen_region


if __name__ == '__main__':
    # 简单的测试代码
    print("测试 window_handler.py...")
    # 你需要在这里填入你实际的游戏窗口标题进行测试
    # test_game_title = "你的游戏窗口标题"
    test_game_title = "大话西游2经典版 $Revision：1774055 - 云水一梦 - 四季春如黛（ID：431061498）"  # 用你之前的标题示例

    # 尝试手动激活游戏窗口，然后再运行这个测试脚本
    print(f"请确保标题为 '{test_game_title}' 的游戏窗口已打开并且可见。")
    time.sleep(3)

    region = find_and_setup_game_window(test_game_title)
    if region:
        print(f"测试成功：获取到游戏区域: {region}")
    else:
        print("测试失败：未能获取到游戏区域。")