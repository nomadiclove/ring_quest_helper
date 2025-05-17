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
            如果找到多个，会尝试根据固定尺寸 (1378x831) 来选择。
            """
            try:
                all_matching_windows = pyautogui.getWindowsWithTitle(self.window_title_pattern)

                if not all_matching_windows:
                    print(f"错误：未找到标题包含 '{self.window_title_pattern}' 的窗口。")
                    self.window = None
                    return None

                if len(all_matching_windows) == 1:
                    # 如果只有一个匹配，我们仍需检查其尺寸是否合理
                    win = all_matching_windows[0]
                    # 允许一定的容差，例如 +/- 5像素
                    if abs(win.width - 1378) <= 5 and abs(win.height - 831) <= 5:
                        self.window = win
                        print(f"成功找到唯一窗口且尺寸匹配: '{self.window.title}', 尺寸: ({self.window.width}x{self.window.height})")
                    else:
                        print(f"找到唯一窗口 '{win.title}'，但其尺寸 ({win.width}x{win.height}) 与预期的 1378x831 不符。")
                        print("请检查游戏窗口是否为预期大小，或是否有其他同名窗口。")
                        # 打印所有窗口以供调试
                        print("当前所有可见窗口标题:")
                        for t_win in pyautogui.getAllWindows():
                            if t_win.title: 
                                print(f"  - '{t_win.title}', 尺寸: ({t_win.width}x{t_win.height})")
                        self.window = None # 尺寸不符，视为未找到
                        return None
                else: # 找到多个窗口
                    print(f"找到多个标题包含 '{self.window_title_pattern}' 的窗口:")
                    potential_main_window = None

                    for i, win in enumerate(all_matching_windows):
                        print(f"  {i+1}. 标题: '{win.title}', 位置: ({win.left},{win.top}), 尺寸: ({win.width}x{win.height})")
                        # 检查尺寸是否非常接近 1378x831 (允许微小误差, e.g., +/- 5 pixels)
                        if abs(win.width - 1378) <= 5 and abs(win.height - 831) <= 5:
                            if potential_main_window is not None:
                                # 如果已找到一个尺寸匹配的，现在又找到一个，说明有问题
                                print(f"警告：找到多个尺寸接近 1378x831 的窗口。这不符合预期。")
                                print(f"  - 已有: '{potential_main_window.title}'")
                                print(f"  - 新的: '{win.title}'")
                                # 这种情况下，我们无法确定哪个是主窗口，选择不返回
                                self.window = None
                                return None 
                            potential_main_window = win

                    if potential_main_window:
                        print(f"根据固定尺寸 1378x831 选择: '{potential_main_window.title}' 作为主窗口。")
                        self.window = potential_main_window
                    else:
                        print(f"在多个匹配窗口中，未能找到尺寸接近 1378x831 的窗口。")
                        self.window = None
                        return None

                if self.window:
                    self._update_geometry()
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
        计算并返回游戏内部画面的区域 (x, y, width, height) 相对于屏幕。
        基于窗口总尺寸 1378x831 和内部游戏画面 1366x768。
        """
        if not self.geometry:
            self.find_window() # 尝试再次查找窗口以获取geometry
            if not self.geometry:
                print("错误：无法获取窗口外部几何信息，不能计算内部区域。")
                return None
      
        # 确保获取到的窗口尺寸是我们预期的，否则偏移计算可能无意义
        # 允许一定的容差
        if not (abs(self.geometry[2] - 1378) <= 5 and abs(self.geometry[3] - 831) <= 5) :
            print(f"警告：当前窗口尺寸 ({self.geometry[2]}x{self.geometry[3]}) 与预期的 1378x831 不符。")
            print("内部区域计算可能不准确。")
            # 即使尺寸不符，也尝试按预期偏移计算，但给出警告
            # 或者这里可以选择返回 None
      
        # X_OFFSET: 从窗口最左边到游戏内部画面最左边的距离 (左边框厚度)
        X_OFFSET = 6  # (1378 - 1366) / 2 假设左右对称
        # Y_OFFSET: 从窗口最顶端到游戏内部画面最顶端的距离 (标题栏 + 上边框厚度)
        Y_OFFSET = 57 # (831 - 768 - 6 (假设下边框也是6)) = 57.  或者直接用用户提供的 28/29.
                      # 如果 Y_OFFSET 是 28, 那么下边框是 63 - 28 = 35
                      # 如果 Y_OFFSET 是 29, 那么下边框是 63 - 29 = 34
                      # 我们先用28，如果截图有偏差再调整
      
        inner_x = self.geometry[0] + X_OFFSET
        inner_y = self.geometry[1] + Y_OFFSET
      
        # 内部固定宽高
        inner_width = 1366
        inner_height = 768
      
        print(f"计算得到的内部游戏区域: X={inner_x}, Y={inner_y}, Width={inner_width}, Height={inner_height}")
        return (inner_x, inner_y, inner_width, inner_height)

      
# --- 测试代码 ---

if __name__ == '__main__':
  print("正在测试 WindowHandler...")
  try:
      handler = WindowHandler()
      print(f"将使用配置文件: {handler.config_path}")
      print(f"将查找窗口标题包含: '{handler.window_title_pattern}'")

      game_window = handler.find_window()

      if game_window:
          print(f"找到的窗口对象: {game_window}")
          print(f"窗口标题: {game_window.title}")
          print(f"窗口外部几何信息 (从handler.geometry获取): {handler.geometry}")

          handler.activate_window()
          pyautogui.sleep(0.5) # 等待窗口激活

          inner_area = handler.get_inner_game_area()
          if inner_area:
              print(f"精确计算的内部游戏区域 (相对于屏幕): X={inner_area[0]}, Y={inner_area[1]}, Width={inner_area[2]}, Height={inner_area[3]}")

              # 取消以下注释来测试截图
              try:
                  screenshot = pyautogui.screenshot(region=inner_area)
                  screenshot_path = "game_inner_area_test.png"
                  screenshot.save(screenshot_path)
                  # 获取绝对路径方便查找
                  abs_path = os.path.abspath(screenshot_path)
                  print(f"已尝试截取内部游戏区域并保存为: {abs_path}")
              except Exception as e:
                  print(f"截图或保存时发生错误: {e}")
      else:
          print("未能找到符合条件的游戏主窗口。请检查：")
          print("1. 游戏是否已运行且窗口大小正常 (约1378x831)？")
          print(f"2. config/settings.ini 中的 WindowTitle ('{handler.window_title_pattern}') 是否正确？")
          print("当前所有可见窗口标题和尺寸:")
          try:
              for win_obj in pyautogui.getAllWindows():
                  if win_obj.title: # 过滤空标题
                      print(f"  - '{win_obj.title}', 尺寸: ({win_obj.width}x{win_obj.height})")
          except Exception as e:
              print(f"获取所有窗口信息时出错: {e}")