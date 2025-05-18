import pyautogui # PyAutoGUI 用于查找和控制窗口

# pyautogui 底层依赖 pygetwindow 来处理窗口，通常不需要直接导入 pygetwindow
# import pygetwindow # 如果需要更底层的窗口操作，可以考虑

def find_game_window(title_pattern, expected_width=None, expected_height=None):
    """
    根据标题模式查找游戏窗口，并可选地根据期望尺寸进行验证。

    参数:
    - title_pattern (str): 窗口标题中应包含的字符串。
    - expected_width (int, optional): 期望的窗口宽度。
    - expected_height (int, optional): 期望的窗口高度。

    返回:
    - pygetwindow.Win32Window (或类似): 找到的窗口对象。
    - None: 如果未找到或尺寸不匹配。
    """
    try:
        windows = pyautogui.getWindowsWithTitle(title_pattern)
    except Exception: # 捕获pyautogui可能抛出的底层异常
        return None # 如果查找时出错，直接返回None

    if not windows:
        return None

    candidate_windows = []
    for window in windows:
        # 确保窗口可见且有实际尺寸 (过滤掉一些特殊窗口)
        if not window.isVisible or window.width <= 0 or window.height <= 0:
            continue

        if expected_width is not None and expected_height is not None:
            # 允许一定的尺寸容差，例如 +/- 5 像素
            if abs(window.width - expected_width) <= 5 and \
               abs(window.height - expected_height) <= 5:
                candidate_windows.append(window)
        else:
            # 如果不提供期望尺寸，则所有标题匹配的都算候选
            candidate_windows.append(window)

    if not candidate_windows:
        return None

    # 如果有多个候选窗口，通常选择最大的那个（或第一个，如果大小都一样）
    # 这里的逻辑可以根据实际情况调整，目前先返回第一个符合条件的
    # 或者，如果严格要求只有一个符合尺寸的，可以在上面循环中直接返回
    if len(candidate_windows) > 1:
        # 如果找到多个完全符合标题和尺寸的，可能需要更复杂的区分逻辑
        # 目前简单返回第一个，或者可以考虑面积最大的
        # sorted_windows = sorted(candidate_windows, key=lambda w: w.width * w.height, reverse=True)
        # return sorted_windows[0]
        pass # 暂时允许返回第一个，如果需要更严格的唯一性，这里可以返回None或抛异常

    return candidate_windows[0]


def activate_window(window_object):
    """
    激活指定的窗口对象，将其带到前台。

    参数:
    - window_object (pygetwindow.Win32Window): 要激活的窗口对象。

    返回:
    - bool: 如果尝试激活成功（不保证一定成功，取决于系统），返回True，否则False。太
    """
    if window_object and hasattr(window_object, 'activate'):
        if not window_object.isActive:
            window_object.activate()
        if window_object.isMinimized:
            window_object.restore()
        return True
    return False
    
def get_window_rect(window_object):
    """
    获取指定窗口对象的屏幕矩形区域。

    参数:
    - window_object (pymanager.py
import pyautogui # PyAutoGUI用于查找和控制窗口

# 全局变量来缓存窗口对象getwindow.Win32Window): 窗口对象。

    返回:
    - tuple: (left, top, width, height) 窗口在屏幕上的位置和尺寸。
    - None: 如果窗口对象无效或无法获取信息和其矩形，避免重复查找，提高效率
_cached_game_window = None
_cached_window_。
    """
    if window_object and \
       hasattr(window_object, 'left') and \
       hasattr(window_object, 'top') and \
       hasattr(window_object, 'width') and \
       hasattr(window_object, 'height'):
        return (window_object.left, window_object.top, window_object.width, window_object.height)

    return None

               
def find_game_window(title_pattern, expected_width, expected_height):
    """
    查找并缓存符合标题和尺寸的游戏窗口。

    返回:
        pyautogui.Window, 'width') and \
       hasattr(window_object, 'height'):
        return (window_object.: 游戏窗口对象，如果找到且尺寸符合。
        None: 如果未找到或尺寸不符。
    """
    global _cached_game_window, _cached_window_rect

    # 如果left, window_object.top, window_object.width, window_object.height)
    return None