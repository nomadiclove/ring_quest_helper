# 文件名: input_simulator.py
# 位置: ring_quest_helper/core/input_simulator.py

import pyautogui
import time
import random

# 可以考虑禁用PyAutoGUI的防错功能，但在调试时请务必小心
# pyautogui.FAILSAFE = False

DEFAULT_CLICK_DURATION = 0.1 # 模拟点击的按下和释放之间的轻微延时
DEFAULT_MOVE_DURATION = 0.2  # 模拟鼠标移动的耗时

def click_at(x, y, button='left', clicks=1, interval=0.1, duration=DEFAULT_CLICK_DURATION):
    """
    在指定屏幕坐标点击鼠标。
    :param x: x坐标
    :param y: y坐标
    :param button: 'left', 'right', 'middle'
    :param clicks: 点击次数
    :param interval: 多次点击之间的间隔（秒）
    :param duration: 每次点击的持续时间（秒），模拟按下的时间
    """
    try:
        # PyAutoGUI的click本身包含了moveTo, mouseDown, mouseUp
        # duration参数在pyautogui.click中指的是每次点击的总时间（从按下到释放）
        # 但为了更细致的控制或如果以后想分开模拟，可以保留自定义duration
        pyautogui.click(x=x, y=y, clicks=clicks, interval=interval, button=button, duration=duration)
        # print(f"DEBUG (InputSimulator): 点击坐标 ({x}, {y}), 按键: {button}, 次数: {clicks}")
    except Exception as e:
        print(f"错误 (InputSimulator): 点击 ({x}, {y}) 时发生: {e}")

def move_to(x, y, duration=DEFAULT_MOVE_DURATION):
    """
    将鼠标移动到指定屏幕坐标。
    :param x: x坐标
    :param y: y坐标
    :param duration: 移动过程的耗时（秒），0表示瞬移
    """
    try:
        pyautogui.moveTo(x, y, duration=duration)
        # print(f"DEBUG (InputSimulator): 鼠标移动到 ({x}, {y})")
    except Exception as e:
        print(f"错误 (InputSimulator): 移动鼠标到 ({x}, {y}) 时发生: {e}")

def drag_to(x, y, duration=0.5, button='left'):
    """
    按住鼠标左键拖拽到指定位置。
    :param x: 目标x坐标
    :param y: 目标y坐标
    :param duration: 拖拽过程的耗时（秒）
    :param button: 按下的鼠标按键
    """
    try:
        pyautogui.dragTo(x, y, duration=duration, button=button)
        # print(f"DEBUG (InputSimulator): 鼠标拖拽到 ({x}, {y})")
    except Exception as e:
        print(f"错误 (InputSimulator): 拖拽鼠标到 ({x}, {y}) 时发生: {e}")

def type_text(text, interval=0.05):
    """
    模拟键盘输入文本。
    :param text: 要输入的字符串。
    :param interval: 每个字符之间的输入间隔（秒）。
    """
    try:
        pyautogui.write(text, interval=interval)
        # print(f"DEBUG (InputSimulator): 输入文本: '{text}'")
    except Exception as e:
        print(f"错误 (InputSimulator): 输入文本 '{text}' 时发生: {e}")

def press_key(key_name):
    """
    模拟按下并释放单个按键。
    对于特殊按键，请参考 PyAutoGUI 的 KEYBOARD_KEYS 文档。
    例如: 'enter', 'esc', 'f1', 'left', 'ctrl', 'shift', 'alt'
    """
    try:
        pyautogui.press(key_name)
        # print(f"DEBUG (InputSimulator): 按下按键: '{key_name}'")
    except Exception as e:
        print(f"错误 (InputSimulator): 按下按键 '{key_name}' 时发生: {e}")

def hotkey(*args):
    """
    模拟按下组合键，例如 hotkey('ctrl', 'c')。
    """
    try:
        pyautogui.hotkey(*args)
        # print(f"DEBUG (InputSimulator): 按下组合键: {args}")
    except Exception as e:
        print(f"错误 (InputSimulator): 按下组合键 {args} 时发生: {e}")

if __name__ == '__main__':
    print("测试 input_simulator.py...")
    print("3秒后将在屏幕 (100,100) 点击，请确保该区域安全。")
    time.sleep(3)
    # click_at(100, 100)
    # time.sleep(1)
    # move_to(200, 200)
    # time.sleep(1)
    # type_text("Hello PyAutoGUI!")
    # time.sleep(1)
    # press_key("enter")
    print("input_simulator.py 模块可被导入和测试。")