import pyautogui
import cv2
import numpy as np
import os
import configparser # 确保导入 configparser
import traceback # 用于打印完整的错误栈

# 相对导入我们自己的模块
from core.window_handler import WindowHandler
from core.image_utils import find_template, find_contours_by_color # 导入两个函数
from core.ocr_utils import recognize_text_from_image_data

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
        screenshot_bgr = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)

        # (可选) 保存一份完整截图到项目根目录
        # screenshot_pil.save("main_test_game_screen.png") 
        # print("内部游戏画面截图已保存为 main_test_game_screen.png")

        # 2. 构建模板图片路径
        base_dir = os.path.dirname(os.path.abspath(__file__)) 
        template_path = os.path.join(base_dir, 'assets', 'templates', 'task_tracker_header.png')

        if not os.path.exists(template_path):
            print(f"错误：模板图片未找到: {template_path}")
            return

        print(f"尝试使用模板图片: {template_path}")

        # 3. 调用 find_template 进行查找 "任务追踪" 标题
        match_result = find_template(screen_image_data=screenshot_bgr, 
                                     template_image_path=template_path, 
                                     threshold=0.7) 

        if match_result:
            header_x, header_y, header_w, header_h, confidence = match_result
            print(f"成功找到 '任务追踪' 标题模板！")
            print(f"  在游戏画面中的相对坐标: X={header_x}, Y={header_y}")
            print(f"  模板尺寸: Width={header_w}, Height={header_h}")
            print(f"  匹配置信度: {confidence:.4f}")
            print("-" * 30)
            print("尝试识别任务类型...")

            # 读取OCR相关的配置
            config = configparser.ConfigParser()
            config_path = os.path.join(base_dir, 'config', 'settings.ini')
            if not os.path.exists(config_path):
                print(f"错误：配置文件 {config_path} 未找到，无法进行OCR。")
                return
            config.read(config_path, encoding='utf-8')

            try:
                task_type_offset_x = config.getint('TaskTrackerUI', 'TaskTypeOffsetX')
                task_type_offset_y = config.getint('TaskTrackerUI', 'TaskTypeOffsetY')
                task_type_region_height = config.getint('TaskTrackerUI', 'TaskTypeRegionHeight')
                task_type_region_width = config.getint('TaskTrackerUI', 'TaskTypeRegionWidth')
            except (configparser.NoSectionError, configparser.NoOptionError, ValueError) as e:
                print(f"错误：配置文件中缺少或格式错误 TaskType UI 相关配置项: {e}")
                return

            # 计算任务类型区域的ROI
            roi_task_type_x = header_x + task_type_offset_x
            roi_task_type_y = header_y + header_h + task_type_offset_y
            roi_task_type_w = task_type_region_width
            roi_task_type_h = task_type_region_height

            print(f"计算得到的任务类型ROI (游戏画面内坐标): X={roi_task_type_x}, Y={roi_task_type_y}, W={roi_task_type_w}, H={roi_task_type_h}")

            if (roi_task_type_x >= 0 and roi_task_type_y >= 0 and
                roi_task_type_x + roi_task_type_w <= screenshot_bgr.shape[1] and
                roi_task_type_y + roi_task_type_h <= screenshot_bgr.shape[0]):

                task_type_roi_image_bgr = screenshot_bgr[roi_task_type_y : roi_task_type_y + roi_task_type_h,
                                                         roi_task_type_x : roi_task_type_x + roi_task_type_w]

                cv2.imwrite("debug_task_type_roi.png", task_type_roi_image_bgr)
                print("任务类型ROI区域已保存为 debug_task_type_roi.png")

                recognized_task_type = recognize_text_from_image_data(task_type_roi_image_bgr, lang='chi_sim', psm=7)

                if recognized_task_type:
                    print(f"识别出的任务类型: '{recognized_task_type}'")

                    # 根据识别出的任务类型执行不同逻辑
                    # 注意：根据你的实际任务调整这里的判断条件
                    if "见多识广" in recognized_task_type or "灵儿" in recognized_task_type: # 假设"灵儿"也属于这类任务的处理流程
                        task_name_for_log = "见多识广/灵儿" # 用于日志
                        if "灵儿" in recognized_task_type and "见多识广" not in recognized_task_type :
                            task_name_for_log = "灵儿"
                        elif "见多识广" in recognized_task_type and "灵儿" not in recognized_task_type:
                             task_name_for_log = "见多识广"

                        print(f"当前任务判断为：{task_name_for_log}")
                        print("-" * 30)
                        print("尝试定位并识别任务描述中的NPC名字...")

                        try:
                            task_desc_offset_y = config.getint('TaskTrackerUI', 'TaskDescriptionOffsetY')
                            task_desc_region_width = config.getint('TaskTrackerUI', 'TaskDescriptionRegionWidth')
                            task_desc_region_height = config.getint('TaskTrackerUI', 'TaskDescriptionRegionHeight')

                            green_lower_str = config.get('TaskTrackerUI', 'NpcNameGreenLowerBound')
                            green_upper_str = config.get('TaskTrackerUI', 'NpcNameGreenUpperBound')
                            npc_green_lower = tuple(map(int, green_lower_str.split(',')))
                            npc_green_upper = tuple(map(int, green_upper_str.split(',')))

                        except (configparser.NoSectionError, configparser.NoOptionError, ValueError) as e:
                            print(f"错误：配置文件中缺少或格式错误 TaskDescriptionUI 或颜色范围相关配置项: {e}")
                            return

                        # 计算任务描述区域的ROI
                        # X坐标：可以与任务类型ROI的X对齐，或者也从配置读取一个TaskDescriptionOffsetX
                        roi_desc_x = roi_task_type_x 
                        roi_desc_y = roi_task_type_y + roi_task_type_h + task_desc_offset_y
                        roi_desc_w = task_desc_region_width
                        roi_desc_h = task_desc_region_height

                        print(f"计算得到的任务描述ROI (游戏画面内坐标): X={roi_desc_x}, Y={roi_desc_y}, W={roi_desc_w}, H={roi_desc_h}")

                        if (roi_desc_x >= 0 and roi_desc_y >= 0 and
                            roi_desc_x + roi_desc_w <= screenshot_bgr.shape[1] and
                            roi_desc_y + roi_desc_h <= screenshot_bgr.shape[0]):

                            task_desc_roi_image_bgr = screenshot_bgr[roi_desc_y : roi_desc_y + roi_desc_h,
                                                                     roi_desc_x : roi_desc_x + roi_desc_w]

                            cv2.imwrite("debug_task_description_roi.png", task_desc_roi_image_bgr)
                            print("任务描述ROI区域已保存为 debug_task_description_roi.png")

                            print(f"使用绿色范围进行查找: Lower={npc_green_lower}, Upper={npc_green_upper}")

                            green_blobs_bboxes = find_contours_by_color(task_desc_roi_image_bgr, 
                                                                        npc_green_lower, 
                                                                        npc_green_upper, 
                                                                        min_contour_area=5) # 使用较小值

                            if green_blobs_bboxes:
                                print(f"在任务描述区域中找到 {len(green_blobs_bboxes)} 个潜在的绿色文本块:")
                                task_desc_roi_with_boxes = task_desc_roi_image_bgr.copy()
                                for i, (gx, gy, gw, gh) in enumerate(green_blobs_bboxes):
                                    print(f"  绿色块 {i+1}: X={gx}, Y={gy}, W={gw}, H={gh} (相对于任务描述ROI)")
                                    cv2.rectangle(task_desc_roi_with_boxes, (gx, gy), (gx + gw, gy + gh), (0, 0, 255), 1)
                                    green_blob_image = task_desc_roi_image_bgr[gy:gy+gh, gx:gx+gw]

                                    cv2.imwrite(f"debug_green_blob_{i+1}.png", green_blob_image)

                                    npc_name_text = recognize_text_from_image_data(green_blob_image, lang='chi_sim', psm=8)
                                    if npc_name_text:
                                        print(f"    识别出的文本: '{npc_name_text}'")
                                        # TODO: 在这里判断是否是目标NPC名字 (例如 "灵儿")
                                        # if "灵儿" in npc_name_text:
                                        #     click_x_game = roi_desc_x + gx + gw // 2
                                        #     click_y_game = roi_desc_y + gy + gh // 2
                                        #     print(f"    准备点击NPC: '{npc_name_text}' 在游戏画面坐标: ({click_x_game}, {click_y_game})")
                                        #     # pyautogui.click(click_x_game + inner_game_area_rect[0], click_y_game + inner_game_area_rect[1])
                                        #     # break # 假设找到并点击后就结束这个任务的处理
                                    else:
                                        print(f"    未能从绿色块 {i+1} 识别出文本。")

                                cv2.imwrite("debug_main_found_green_blobs.png", task_desc_roi_with_boxes)
                                print("带有标记的绿色区域块图片已保存为 debug_main_found_green_blobs.png")
                            else:
                                print("在任务描述区域中未能找到符合条件的绿色文本块。请检查相关配置。")
                        else:
                            print("错误：计算得到的任务描述ROI超出了截图范围。")
                    else:
                        print(f"当前任务类型 '{recognized_task_type}' 不是需要特殊处理的类型，脚本继续或结束。")
                else:
                    print("未能识别出任务类型文本。请检查ROI切割和OCR参数。")
            else:
                print("错误：计算得到的任务类型ROI超出了截图范围。")
        else:
            print("未能找到 '任务追踪' 标题模板。请检查相关配置和游戏界面。")

    except Exception as e:
        print(f"脚本执行过程中发生未预料的错误: {e}")
        traceback.print_exc() # 打印完整的错误栈信息

if __name__ == '__main__':
    main()