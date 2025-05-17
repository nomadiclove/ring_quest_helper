import configparser
import pyautogui
import os # 导入os模块以构建跨平台的文件路径

class WindowHandler:
    def __init__(self, config_path=None):
        if config_path is None:
            # 构建到项目根目录下 config/settings.ini 的路径
            # __file__ 是当前脚本的路径
            # os.path.dirname(__file__) 是当前脚本所在的目录 (core)
            # os.path.join(..., '..') 回到上一级目录 (项目根目录)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_path = os.path.join(base_dir, 'config', 'settings.ini')
        else:
            self.config_path = config_path

        self.config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        self.config.read(self.config_path, encoding='utf-8') # 指定UTF-8编码读取

        try:
            self.window_title_pattern = self.config.get('GameWindow', 'WindowTitle')
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise ValueError(f"配置文件中缺少 GameWindow.WindowTitle: {e}")

        self.window = None # 存储找到的窗口对象
        self.geometry = None # 存储窗口的几何信息 (x, y, width, height)

    def find_window(self):
        """
        根据配置文件中的标题查找游戏窗口。
        """
        try:
            # pyautogui.getWindowsWithTitle() 返回一个列表，即使只找到一个
            windows = pyautogui.getWindowsWithTitle(self.window_title_pattern)
            if not windows:
                print(f"错误：未找到标题包含 '{self.window_title_pattern}' 的窗口。")
                self.window = None
                return None

            # 通常我们假设只有一个匹配的主窗口，或者取第一个
            # 如果有多个完全匹配的窗口，可能需要更复杂的逻辑来区分
            self.window = windows[0] 
            print(f"成功找到窗口: '{self.window.title}'")
            self._update_geometry() # 找到窗口后更新其几何信息
            return self.window
        except Exception as e:
            print(f"查找窗口时发生错误: {e}")
            self.window = None
            return None

    def _update_geometry(self):
        """
        更新已找到窗口的几何信息 (x, y, width, height)。
        这是指整个窗口的外部尺寸。
        """
        if self.window:
            try:
                # pyautogui 的窗口对象有 left, top, width, height 属性
                self.geometry = (self.window.left, self.window.top, self.window.width, self.window.height)
                print(f"窗口外部几何信息: X={self.geometry[0]}, Y={self.geometry[1]}, Width={self.geometry[2]}, Height={self.geometry[3]}")
            except Exception as e:
                print(f"获取窗口几何信息时发生错误: {e}")
                self.geometry = None
        else:
            self.geometry = None


    def activate_window(self):
        """
        激活找到的游戏窗口，将其带到前台。
        """
        if self.window:
            try:
                if not self.window.isActive:
                    self.window.activate()
                # 有些系统可能需要额外的操作来确保窗口完全置顶
                # self.window.maximize() # 如果需要最大化
                # self.window.restore() # 如果之前是最小化或最大化，恢复到正常大小
                # pyautogui.sleep(0.1) # 短暂等待确保操作完成
                print(f"窗口 '{self.window.title}' 已尝试激活。")
                return True
            except Exception as e:
                # pyautogui 的窗口对象可能没有 isActive 属性或 activate 方法，具体取决于底层库 (pygetwindow)
                # 对于更可靠的激活，可能需要特定平台的库如 pywin32
                print(f"激活窗口时发生错误 (可能pyautogui不支持此操作或窗口已关闭): {e}")
                try:
                    # 备用激活方式 (有时更有效)
                    self.window.minimize()
                    self.window.restore()
                    self.window.focus() # pygetwindow 的 focus()
                    print(f"窗口 '{self.window.title}' 已尝试通过备用方式激活。")
                    return True
                except Exception as e2:
                    print(f"备用激活窗口方式也失败: {e2}")
                    return False
        else:
            print("错误：未找到窗口，无法激活。")
            return False

    def get_inner_game_area(self):
        """
        计算并返回游戏内部画面的区域 (x, y, width, height)。
        目前这是一个占位符，需要根据实际情况调整。
        """
        if not self.geometry:
            print("错误：无法获取窗口外部几何信息，不能计算内部区域。")
            return None

        # TODO: 根据用户描述，外部窗口比内部1366x768大。
        # 我们需要确定标题栏和边框的厚度。
        # 假设：
        # title_bar_height = 30  # 估算值，需要用户测量
        # border_thickness_left = 5 # 估算值
        # border_thickness_right = 5 # 估算值
        # border_thickness_bottom = 5 # 估算值

        # inner_x = self.geometry[0] + border_thickness_left
        # inner_y = self.geometry[1] + title_bar_height
        # inner_width = 1366 # 根据用户描述固定
        # inner_height = 768 # 根据用户描述固定
        
        # 另一种思路：如果外部窗口大小是固定的，并且内部大小也是固定的
        # 那么偏移量也是固定的。
        # 或者，如果窗口的 client area 可以直接获取，那是最好的。

        print("注意: get_inner_game_area() 当前是占位符，需要精确实现。")
        # 暂时返回整个窗口区域减去一些估算值，或者直接返回固定值（如果窗口位置固定）
        # 更可靠的做法是让用户测量或使用工具获取精确偏移
        
        # 作为一个非常初步的假设，如果游戏窗口总是最大化或者固定大小，
        # 并且其左上角是 (self.geometry[0], self.geometry[1])
        # 那么内部区域的左上角相对于屏幕的坐标，需要减去标题栏和左边框
        # inner_x = self.geometry[0] + X_OFFSET_FROM_WINDOW_LEFT_TO_GAME_AREA_LEFT
        # inner_y = self.geometry[1] + Y_OFFSET_FROM_WINDOW_TOP_TO_GAME_AREA_TOP
        # return (inner_x, inner_y, 1366, 768)
        
        # 目前，我们先返回外部几何信息，提示用户这部分需要精确化
        print("将暂时返回外部窗口的左上角坐标加上固定的1366x768作为内部区域参考，这通常不准确。")
        return (self.geometry[0], self.geometry[1], 1366, 768)


# --- 测试代码 ---
if __name__ == '__main__':
    print("正在测试 WindowHandler...")
    # 确保你的 config/settings.ini 文件中的 WindowTitle 设置正确
    # 例如: WindowTitle = 大话西游2经典版

    try:
        handler = WindowHandler()
        print(f"将使用配置文件: {handler.config_path}")
        print(f"将查找窗口标题包含: '{handler.window_title_pattern}'")

        game_window = handler.find_window()

        if game_window:
            print(f"找到的窗口对象: {game_window}")
            print(f"窗口标题: {game_window.title}") # 打印实际匹配到的完整标题
            print(f"窗口外部几何信息 (从handler.geometry获取): {handler.geometry}")
            
            # 尝试激活窗口
            handler.activate_window()
            pyautogui.sleep(1) # 等待1秒，看看窗口是否到最前

            # 获取（当前占位的）内部游戏区域
            inner_area = handler.get_inner_game_area()
            if inner_area:
                print(f"估算的内部游戏区域 (相对于屏幕): X={inner_area[0]}, Y={inner_area[1]}, Width={inner_area[2]}, Height={inner_area[3]}")
                # 后续截图可以基于这个 inner_area
                # screenshot = pyautogui.screenshot(region=inner_area)
                # screenshot.save("game_inner_area_test.png")
                # print("已尝试截取内部游戏区域并保存为 game_inner_area_test.png")

        else:
            print("未能找到游戏窗口。请检查：")
            print("1. 游戏是否已运行？")
            print(f"2. config/settings.ini 中的 WindowTitle ('{handler.window_title_pattern}') 是否与游戏窗口标题的一部分精确匹配？")
            print("   (注意大小写，如果 pyautogui 区分的话)")
            all_titles = pyautogui.getAllTitles()
            print("当前所有可见窗口标题:")
            for t in all_titles:
                if t: # 过滤空标题
                    print(f"  - {t}")

    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"测试过程中发生未预料的错误: {e}")