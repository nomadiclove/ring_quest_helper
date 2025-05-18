import pyautogui
import time # 用于可能的延时

# pyautogui 的一些全局设置，可以根据需要调整
# pyautogui.PAUSE = 0.05  # 在每次pyautogui函数调用后自动暂停的秒数，有助于操作更稳定
# pyautogui.FAILSAFE = True # 将鼠标移到屏幕左上角会触发FailSafeException，终止脚本

def click_screen_coords(screen_x, screen_y, button='left', clicks=1, interval=0.1, duration=0.1):
    """
    在屏幕的指定绝对坐标处模拟鼠标点击。

    参数:
    - screen_x (int): 点击位置的屏幕X坐标。
    - screen_y (int): 点击位置的屏幕Y坐标。
    - button (str): 'left', 'middle', 'right'。
    - clicks (int): 点击次数。
    - interval (float): 多次点击之间的间隔秒数。
    - duration (float): 鼠标移动到目标位置并完成点击的总耗时（近似值）。
                       较小的值意味着更快的点击。
    """
    try:
        # 先将鼠标移动到目标位置，然后点击
        # duration 控制移动速度，可以设为0实现瞬移后点击
        pyautogui.moveTo(screen_x, screen_y, duration=duration / 2 if clicks == 1 else 0) # 如果多次点击，瞬移
        pyautogui.click(x=screen_x, y=screen_y, 
                        clicks=clicks, interval=interval, 
                        button=button, duration=duration / 2 if clicks == 1 else 0.05) # duration用于单次点击的按下释放过程
    except pyautogui.FailSafeException:
        # print("FailSafe triggered: 鼠标移动到屏幕左上角，脚本终止。") # 暂时不打印
        raise # 重新抛出异常，让调用者知道发生了什么
    except Exception: # 捕获其他可能的pyautogui错误
        # print(f"错误 (click_screen_coords): 点击操作失败 - {e}") # 暂时不打印
        pass # 根据你的原则，暂时不处理，让它静默失败或由调用者处理


def press_key(key_name_or_list, presses=1, interval=0.1):
    """
    模拟按下并释放一个或多个按键。

    参数:
    - key_name_or_list (str or list): 单个按键名称 (例如 'enter', 'f1', 'a', 'ctrl')
                                     或一个按键名称列表 (用于组合键，例如 ['ctrl', 'c']，
                                     或者用于依次按下多个键，但pyautogui.hotkey更适合组合键)。
                                     对于组合键，推荐使用 press_hotkey。
    - presses (int): 按键次数。
    - interval (float): 多次按键之间的间隔秒数。
    """
    try:
        if isinstance(key_name_or_list, list):
            # 如果是列表，pyautogui.press会依次按下它们
            # 但对于组合键，hotkey更好
            for _ in range(presses):
                pyautogui.press(key_name_or_list)
                if presses > 1 and interval > 0:
                    time.sleep(interval)
        else: # 单个按键
            pyautogui.press(key_name_or_list, presses=presses, interval=interval)
    except Exception:
        # print(f"错误 (press_key): 按键操作失败 - {e}") # 暂时不打印
        pass


def press_hotkey(*args):
    """
    模拟按下组合键 (例如 Ctrl+C, Alt+Tab)。
    参数会直接传递给 pyautogui.hotkey()。

    参数:
    - *args: 任意数量的按键名称字符串，例如 press_hotkey('ctrl', 'alt', 'delete')。
    """
    try:
        pyautogui.hotkey(*args)
    except Exception:
        # print(f"错误 (press_hotkey): 组合键操作失败 - {e}") # 暂时不打印
        pass

# (可选) 其他鼠标操作函数
def move_to_screen_coords(screen_x, screen_y, duration=0.25):
    """模拟鼠标移动到屏幕指定坐标。"""
    try:
        pyautogui.moveTo(screen_x, screen_y, duration=duration)
    except pyautogui.FailSafeException:
        raise
    except Exception:
        pass

# def drag_to_screen_coords(screen_x, screen_y, duration=0.5, button='left'):
#     """模拟鼠标拖拽到屏幕指定坐标。"""
#     try:
#         pyautogui.dragTo(screen_x, screen_y, duration=duration, button=button)
#     except pyautogui.FailSafeException:
#         raise
#     except Exception:
#         pass