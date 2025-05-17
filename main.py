import pyautogui # 用于截图时的颜色转换，以及可能的延时
import cv2 # 用于将 Pillow Image 转换为 NumPy array
from PIL import Image # Pyautogui screenshot 返回的是 Pillow Image
import os
import configparser

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
            header_x, header_y, header_w, header_h, confidence = match_result
            print(f"成功找到 '任务追踪' 标题模板！")
            print(f"  在游戏画面中的相对坐标: X={header_x}, Y={header_y}")
            print(f"  模板尺寸: Width={header_w}, Height={header_h}")
            print(f"  匹配置信度: {confidence:.4f}")
    
            # --- 新增：识别任务类型 ---
            print("-" * 30) # 分隔符
            print("尝试识别任务类型...")
    
            # 1. 读取OCR相关的配置
            config = configparser.ConfigParser()
            config_path = os.path.join(base_dir, 'config', 'settings.ini')
            if not os.path.exists(config_path):
                print(f"错误：配置文件 {config_path} 未找到，无法进行OCR。")
                return
            config.read(config_path, encoding='utf-8')
    
            try:
                task_type_offset_y = config.getint('TaskTrackerUI', 'TaskTypeOffsetY')
                task_type_region_height = config.getint('TaskTrackerUI', 'TaskTypeRegionHeight')
                task_type_region_width = config.getint('TaskTrackerUI', 'TaskTypeRegionWidth')
            except (configparser.NoSectionError, configparser.NoOptionError) as e:
                print(f"错误：配置文件中缺少 TaskTrackerUI 相关配置项: {e}")
                return
    
            # 2. 计算任务类型区域的ROI (相对于1366x768游戏画面)
            # ROI的左上角x坐标可以与header_x对齐，或者稍微向左一点，如果任务类型文本可能更靠左
            # 我们先假设与header_x对齐，或者可以从配置中读取一个X偏移
            task_type_offset_x = config.getint('TaskTrackerUI', 'TaskTypeOffsetX')
            
            roi_task_type_x = header_x + task_type_offset_x
            roi_task_type_y = header_y + header_h + task_type_offset_y
            roi_task_type_w = task_type_region_width
            roi_task_type_h = task_type_region_height
    
            print(f"计算得到的任务类型ROI (游戏画面内坐标): X={roi_task_type_x}, Y={roi_task_type_y}, W={roi_task_type_w}, H={roi_task_type_h}")
    
            # 3. 从完整游戏画面截图中提取ROI图像数据
            # 确保ROI坐标在截图范围内
            if (roi_task_type_x >= 0 and roi_task_type_y >= 0 and
                roi_task_type_x + roi_task_type_w <= screenshot_bgr.shape[1] and # shape[1] is width
                roi_task_type_y + roi_task_type_h <= screenshot_bgr.shape[0]):   # shape[0] is height
    
                task_type_roi_image_bgr = screenshot_bgr[roi_task_type_y : roi_task_type_y + roi_task_type_h,
                                                         roi_task_type_x : roi_task_type_x + roi_task_type_w]
    
                # (可选) 保存一下这个ROI截图，方便调试ROI是否正确
                cv2.imwrite("debug_task_type_roi.png", task_type_roi_image_bgr)
                print("任务类型ROI区域已保存为 debug_task_type_roi.png")
    
                # 4. 调用OCR函数进行识别
                # 需要从 core.ocr_utils 导入函数
                from core.ocr_utils import recognize_text_from_image_data 
    
                # 对于任务类型这种短文本，PSM=7 (单行文本) 或 PSM=13 (原始单行) 可能效果更好
                # PSM=6 也可以尝试
                recognized_task_type = recognize_text_from_image_data(task_type_roi_image_bgr, lang='chi_sim', psm=7)
    
                if recognized_task_type:
                    print(f"识别出的任务类型: '{recognized_task_type}'")
                    # 后续可以根据这个类型执行不同逻辑
                    if "见多识广" in recognized_task_type:
                        print("当前任务是：见多识广")
                        # TODO: 执行见多识广任务的后续步骤
                    # elif "其他任务类型" in recognized_task_type:
                        # ...
                else:
                    print("未能识别出任务类型文本。请检查：")
                    print("  1. ROI区域是否准确切割到了任务类型文本？(查看 debug_task_type_roi.png)")
                    print("  2. OCR预处理或PSM模式是否需要调整？")
                    print("  3. 配置文件中的偏移和尺寸是否准确？")
            else:
                print("错误：计算得到的任务类型ROI超出了截图范围。请检查配置参数和模板匹配结果。")
                print(f"截图尺寸: W={screenshot_bgr.shape[1]}, H={screenshot_bgr.shape[0]}")
    
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