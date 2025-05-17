import pyautogui # 用于截图时的颜色转换，以及可能的延时
import cv2 # 用于将 Pillow Image 转换为 NumPy array
from PIL import Image # Pyautogui screenshot 返回的是 Pillow Image
import os

# 相对导入我们自己的模块
from core.window_handler import WindowHandler
from core.image_utils import find_template # 导入我们刚创建的函数

def main():
    print("自动化脚本启动...")
    try:
        wh = WindowHandler()
        game_window = wh.find_window()

        if not game_window:
            print("未能找到游戏窗口，脚本退出。")
            return

        print("尝试激活游戏窗口...")
        wh.activate_window()
        pyautogui.sleep(0.5) # 给点时间让窗口激活

        inner_game_area_rect = wh.get_inner_game_area()
        if not inner_game_area_rect:
            print("未能获取内部游戏区域，脚本退出。")
            return

        print(f"内部游戏区域 (屏幕坐标): {inner_game_area_rect}")

        # 1. 截取内部游戏画面
        print("正在截取内部游戏画面...")
        screenshot_pil = pyautogui.screenshot(region=inner_game_area_rect)

        # 将 Pillow Image 转换为 OpenCV BGR NumPy array
        # Pillow (PIL) Image is RGB, OpenCV is BGR by default
        screenshot_bgr = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)

        # 保存一份截图到项目根目录，方便查看截图内容是否正确
        # (这部分与 window_handler 中的测试截图功能重叠，可以选择保留一个或都保留用于不同阶段调试)
        # screenshot_pil.save("main_test_game_screen.png") 
        # print("内部游戏画面截图已保存为 main_test_game_screen.png")

        # 2. 构建模板图片路径
        base_dir = os.path.dirname(os.path.abspath(__file__)) # main.py 所在的目录 (项目根目录)
        template_path = os.path.join(base_dir, 'assets', 'templates', 'task_tracker_header.png')

        if not os.path.exists(template_path):
            print(f"错误：模板图片未找到: {template_path}")
            print("请确保 'task_tracker_header.png' 已放置在 'assets/templates/' 目录下并已推送到仓库。")
            return

        print(f"尝试使用模板图片: {template_path}")

        # 3. 调用 find_template 进行查找
        # 使用一个相对宽松的阈值进行初步测试，如果误匹配再调高
        match_result = find_template(screen_image_data=screenshot_bgr, 
                                     template_image_path=template_path, 
                                     threshold=0.7) 

        if match_result:
            x, y, w, h, confidence = match_result
            print(f"成功找到 '任务追踪' 标题模板！")
            print(f"  在游戏画面中的相对坐标: X={x}, Y={y}")
            print(f"  模板尺寸: Width={w}, Height={h}")
            print(f"  匹配置信度: {confidence:.4f}")

            # 可选：在截图上画出匹配区域并显示/保存 (用于调试)
            # cv2.rectangle(screenshot_bgr, (x, y), (x + w, y + h), (0, 0, 255), 2) # 红色框
            # cv2.putText(screenshot_bgr, f'{confidence:.2f}', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
            # cv2.imwrite("main_test_match_result.png", screenshot_bgr)
            # print("带有匹配结果的截图已保存为 main_test_match_result.png")

        else:
            print("未能找到 '任务追踪' 标题模板。请检查：")
            print("  1. 模板图片 'task_tracker_header.png' 是否清晰且准确？")
            print("  2. 游戏中的 '任务追踪' UI 是否可见？")
            print("  3. threshold (当前为0.7) 是否设置过高？可以尝试调低一点测试，比如0.6。")
            print("  4. 截图内容是否正确？(可以查看 main_test_game_screen.png)")


    except Exception as e:
        print(f"脚本执行过程中发生未预料的错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # 需要导入 numpy 以便转换截图
    import numpy as np 
    main()