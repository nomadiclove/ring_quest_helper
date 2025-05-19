# core/window_manager.py
import pyautogui

def find_game_window(title_pattern, expected_width, expected_height):
    """
    Finds a game window by title pattern and expected dimensions.
    No caching is used in this version for direct debugging.
    """
    print(f"DEBUG (wm): Entering find_game_window, title_pattern='{title_pattern}', expected_size={expected_width}x{expected_height}")

    found_window_obj = None

    # pyautogui.getWindowsWithTitle 可能会抛出异常，但根据原则我们不在这里try-except
    windows = pyautogui.getWindowsWithTitle(title_pattern)
    if not windows:
        print("DEBUG (wm): pyautogui.getWindowsWithTitle returned no windows.")
        return None

    print(f"DEBUG (wm): pyautogui.getWindowsWithTitle found {len(windows)} window(s).")
    candidate_windows = []
    for i, window in enumerate(windows):
        win_title = getattr(window, 'title', 'N/A')
        win_width = getattr(window, 'width', 0)
        win_height = getattr(window, 'height', 0)

        print(f"DEBUG (wm):  Checking candidate {i+1}: '{win_title}', W={win_width}, H={win_height}")

        if not (win_width > 0 and win_height > 0):
            print(f"DEBUG (wm):    Candidate {i+1} has invalid dimensions, skipping.")
            continue

        width_match = abs(win_width - expected_width) <= 5
        height_match = abs(win_height - expected_height) <= 5

        print(f"DEBUG (wm):    Candidate {i+1} - Width match ({win_width} vs {expected_width}): {width_match}, "
              f"Height match ({win_height} vs {expected_height}): {height_match}")

        if width_match and height_match:
            print(f"DEBUG (wm):    Candidate {i+1} dimensions match!")
            candidate_windows.append(window)
        else:
            print(f"DEBUG (wm):    Candidate {i+1} dimensions do not match, skipping.")

    if not candidate_windows:
        print("DEBUG (wm): No candidate windows passed the dimension filter.")
        return None

    print(f"DEBUG (wm): {len(candidate_windows)} candidate window(s) passed dimension filter.")
    found_window_obj = candidate_windows[0] 
    print(f"DEBUG (wm): Selected window: '{getattr(found_window_obj, 'title', 'N/A')}'")

    return found_window_obj

def activate_window(window_object):
    """
    Activates the specified window object.
    Returns True if activation was attempted, False otherwise.
    """
    if window_object and hasattr(window_object, 'activate'):
        # No try-except per principle, errors will propagate
        if hasattr(window_object, 'isActive') and not window_object.isActive:
            window_object.activate()
        elif not hasattr(window_object, 'isActive'):
             window_object.activate()

        if hasattr(window_object, 'isMinimized') and window_object.isMinimized:
            window_object.restore()
        if hasattr(window_object, 'focus'): 
             window_object.focus()
        return True
    return False

def get_window_rect(window_object):
    """
    Gets the screen rectangle (left, top, width, height) of the window object.
    Returns None if attributes are missing or window_object is None.
    """
    if window_object and \
       hasattr(window_object, 'left') and \
       hasattr(window_object, 'top') and \
       hasattr(window_object, 'width') and \
       hasattr(window_object, 'height'):
        return (window_object.left, window_object.top, window_object.width, window_object.height)
    return None