import pyautogui # 用于截图时的颜色转换，以及可能的延时
import cv2 # 用于将 Pillow Image 转换为 NumPy array
from PIL import Image # Pyautogui screenshot 返回的是 Pillow Image
import os
import configparser
from core.image_utils import find_contours_by_color 

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
                        print("-" * 30)
                        print("尝试定位并识别任务描述中的NPC名字...")
    
                        # 读取任务描述区域的配置
                        try:
                            task_desc_offset_y = config.getint('TaskTrackerUI', 'TaskDescriptionOffsetY')
                            task_desc_region_width = config.getint('TaskTrackerUI', 'TaskDescriptionRegionWidth')
                            task_desc_region_height = config.getint('TaskTrackerUI', 'TaskDescriptionRegionHeight')
    
                            # 读取绿色范围配置 (作为字符串，然后解析)
                            # green_lower_str = config.get('TaskTrackerUI', 'NpcNameGreenLowerBound')
                            # green_upper_str = config.get('TaskTrackerUI', 'NpcNameGreenUpperBound')
                            # npc_green_lower = tuple(map(int, green_lower_str.split(',')))
                            # npc_green_upper = tuple(map(int, green_upper_str.split(',')))
    
                        except (configparser.NoSectionError, configparser.NoOptionError, ValueError) as e:
                            print(f"错误：配置文件中缺少或格式错误 TaskDescriptionUI 或颜色范围相关配置项: {e}")
                            return # 或者continue到下一个循环 (如果是在循环中)
    
                        # 计算任务描述区域的ROI
                        # roi_task_type_y 和 roi_task_type_h 是之前计算的任务类型ROI的y和高
                        # X坐标：我们可以让它和任务类型区域的X坐标对齐
                        roi_desc_x = roi_task_type_x 
                        roi_desc_y = roi_task_type_y + roi_task_type_h + task_desc_offset_y
                        roi_desc_w = task_desc_region_width
                        roi_desc_h = task_desc_region_height
    
                        print(f"计算得到的任务描述ROI (游戏画面内坐标): X={roi_desc_x}, Y={roi_desc_y}, W={roi_desc_w}, H={roi_desc_h}")
    
                        # 从完整游戏画面截图中提取任务描述ROI图像数据
                        if (roi_desc_x >= 0 and roi_desc_y >= 0 and
                            roi_desc_x + roi_desc_w <= screenshot_bgr.shape[1] and
                            roi_desc_y + roi_desc_h <= screenshot_bgr.shape[0]):
    
                            task_desc_roi_image_bgr = screenshot_bgr[roi_desc_y : roi_desc_y + roi_desc_h,
                                                                     roi_desc_x : roi_desc_x + roi_desc_w]
    
                            cv2.imwrite("debug_task_description_roi.png", task_desc_roi_image_bgr)
                            print("任务描述ROI区域已保存为 debug_task_description_roi.png")
    
                            # TODO: 接下来在这里调用 image_utils 中的颜色查找函数
                            # 和 ocr_utils 中的识别函数来处理 task_desc_roi_image_bgr
                            print("下一步：在此区域内查找绿色NPC名字。")

                        try:
                            green_lower_str = config.get('TaskTrackerUI', 'NpcNameGreenLowerBound')
                            green_upper_str = config.get('TaskTrackerUI', 'NpcNameGreenUpperBound')
                            npc_green_lower = tuple(map(int, green_lower_str.split(',')))
                            npc_green_upper = tuple(map(int, green_upper_str.split(',')))
                        except (configparser.NoSectionError, configparser.NoOptionError, ValueError) as e:
                            print(f"错误：配置文件中缺少或格式错误 NpcNameGreenLowerBound/UpperBound 配置项: {e}")
                            return

                        print(f"使用绿色范围进行查找: Lower={npc_green_lower}, Upper={npc_green_upper}")
                        # 在任务描述ROI中查找绿色轮廓
                        # min_contour_area 可以根据实际情况调整，以过滤掉太小的绿色噪点
                        green_blobs_bboxes = find_contours_by_color(task_desc_roi_image_bgr, 
                                                                    npc_green_lower, 
                                                                    npc_green_upper, 
                                                                    min_contour_area=15) # 初始值，可以调整
                        if green_blobs_bboxes:
                            print(f"在任务描述区域中找到 {len(green_blobs_bboxes)} 个潜在的绿色文本块:")

                            # 创建一个副本用于绘制调试框
                            task_desc_roi_with_boxes = task_desc_roi_image_bgr.copy()

                            for i, (gx, gy, gw, gh) in enumerate(green_blobs_bboxes):
                                print(f"  绿色块 {i+1}: X={gx}, Y={gy}, W={gw}, H={gh} (相对于任务描述ROI)")

                                # 在副本上画框
                                cv2.rectangle(task_desc_roi_with_boxes, (gx, gy), (gx + gw, gy + gh), (0, 0, 255), 1) # 红色框

                                # 切割出这个绿色块进行OCR
                                green_blob_image = task_desc_roi_image_bgr[gy:gy+gh, gx:gx+gw]

                                # (可选) 保存每个小绿色块的图片用于调试OCR
                                # cv2.imwrite(f"debug_green_blob_{i+1}.png", green_blob_image)

                                # 对绿色块进行OCR
                                # PSM模式可能需要调整，对于单个词或短语，7, 8, 13 比较常用
                                npc_name_text = recognize_text_from_image_data(green_blob_image, lang='chi_sim', psm=8)

                                if npc_name_text:
                                    print(f"    识别出的文本: '{npc_name_text}'")
                                    # TODO: 在这里判断是否是目标NPC名字，然后计算点击坐标并点击
                                    # 例如，如果 npc_name_text == "贾 有钱" (注意空格可能存在)
                                    # 点击坐标 (相对于游戏画面1366x768的左上角):
                                    # click_x_game = roi_desc_x + gx + gw // 2 # 点击块的中心
                                    # click_y_game = roi_desc_y + gy + gh // 2
                                    # print(f"    准备点击NPC: '{npc_name_text}' 在游戏画面坐标: ({click_x_game}, {click_y_game})")
                                    # input_controller.click_game_coordinate(click_x_game, click_y_game) # 假设有这个函数
                                else:
                                    print(f"    未能从绿色块 {i+1} 识别出文本。")

                            # 保存带有所有框的调试图片
                            cv2.imwrite("debug_main_found_green_blobs.png", task_desc_roi_with_boxes)
                            print("带有标记的绿色区域块图片已保存为 debug_main_found_green_blobs.png")

                        else:
                            print("在任务描述区域中未能找到符合条件的绿色文本块。请检查：")
                            print("  1. 配置文件中的绿色范围 (NpcNameGreenLowerBound/UpperBound) 是否准确？")
                            print("  2. 任务描述中当前是否有绿色的NPC名字？")
                            print("  3. min_contour_area 是否设置过大？")
                      
    
                        
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