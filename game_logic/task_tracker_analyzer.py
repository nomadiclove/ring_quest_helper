# 文件名: task_tracker_analyzer.py
# 位置: ring_quest_helper/game_logic/task_tracker_analyzer.py

import os
import re
from PIL import Image

# 从core模块导入需要的工具函数
# 注意：我们现在在 game_logic 包内，core 和 tasks 是它的兄弟包（如果 main.py 在根目录运行）
# 或者，如果 main.py 确保了项目根目录在 sys.path，我们可以用绝对路径
from core.image_utils import find_image, take_screenshot
from core.ocr_utils import ocr_image_region
from core.opencv_utils import find_green_underlined_link_opencv

def analyze_task_tracker(game_screen_region, config, assets_base_path, loop_num, target_task_keywords_map, item_keywords_map):
    """
    分析任务追踪区域，提取当前任务信息。
    :param game_screen_region: 由 window_handler 返回的，核心游戏画面的 (x,y,w,h) 区域。
    :param config: 已加载的 configparser 对象。
    :param assets_base_path: 资源文件基础路径。
    :param loop_num: 当前循环次数，用于调试。
    :param target_task_keywords_map: 任务类型关键字映射。
    :param item_keywords_map: 物品关键字映射。
    :return: 一个包含任务信息的字典，例如:
             {
                 "found_task_name": "任务名" or None,
                 "ocr_full_description": "完整OCR描述" or "",
                 "full_content_roi_pil_image": PIL Image object of content ROI or None,
                 "task_tracker_content_roi_tuple": (x,y,w,h) of content ROI or None,
                 "npc_link_screen_coords": (screen_x, screen_y) or None
             }
             如果关键步骤失败，则返回 None。
    """
    print("\n--- 分析任务追踪 ---")
    analysis_result = {
        "found_task_name": None,
        "ocr_full_description": "",
        "full_content_roi_pil_image": None,
        "task_tracker_content_roi_tuple": None,
        "npc_link_screen_coords": None
    }

    # 从配置获取参数 (如果参数在config中定义，否则使用默认值)
    default_confidence = float(config.get('General', 'DefaultConfidence', fallback='0.8'))
    ocr_psm_first = int(config.get('OCR', 'PSM_Mode_FirstLine', fallback='7'))
    ocr_psm_full = int(config.get('OCR', 'PSM_Mode_FullDesc', fallback='3'))
    ocr_gap = int(config.get('OCR', 'FirstLineGap', fallback='5'))
    ocr_line_h = int(config.get('OCR', 'FirstLineHeight', fallback='20'))
    ocr_scale = int(config.get('OCR', 'ScaleFactor', fallback='3'))

    h_min = int(config.get('HSV_Green', 'H_Min', fallback='50'))
    s_min = int(config.get('HSV_Green', 'S_Min', fallback='100'))
    v_min = int(config.get('HSV_Green', 'V_Min', fallback='100'))
    h_max = int(config.get('HSV_Green', 'H_Max', fallback='75'))
    s_max = int(config.get('HSV_Green', 'S_Max', fallback='255'))
    v_max = int(config.get('HSV_Green', 'V_Max', fallback='255'))
    lower_green = np.array([h_min, s_min, v_min])
    upper_green = np.array([h_max, s_max, v_max])


    # 1. 查找任务追踪标头 (在给定的 game_screen_region 内)
    header_img_name = config.get('UI_Anchors', 'TaskTrackerHeader', fallback=None)
    if not header_img_name: print("错误 (Analyzer): TaskTrackerHeader 未在config.ini中配置。"); return None
    header_img_path = os.path.join(assets_base_path, header_img_name)

    print(f"DEBUG (Analyzer): 在区域 {game_screen_region} 内查找标头 '{header_img_name}'...")
    header_loc = find_image(header_img_path, confidence=default_confidence, region=game_screen_region)
    if not header_loc: print("错误 (Analyzer): 未找到任务追踪标头。"); return None
    print(f"DEBUG (Analyzer): 找到标头，中心: ({header_loc.x}, {header_loc.y})")

    # 2. 计算内容ROI并截图
    bar_w = int(config.get('TaskTrackerLayout', 'ActualBarWidth', fallback='230')) # 从配置读取或用默认
    bar_h = int(config.get('TaskTrackerLayout', 'ActualBarHeight', fallback='22'))
    content_h = int(config.get('TaskTrackerLayout', 'ContentAreaHeight', fallback='100'))

    roi_tl_x = header_loc.x - bar_w // 2
    roi_tl_y = header_loc.y - bar_h // 2 + bar_h # 标头底部作为内容区顶部
    content_roi_tuple = (int(roi_tl_x), int(roi_tl_y), int(bar_w), int(content_h))
    print(f"DEBUG (Analyzer): 计算得到的内容ROI: {content_roi_tuple}")

    # 使用 image_utils 中的 take_screenshot
    full_content_pil = take_screenshot(
        region=content_roi_tuple,
        save_path=os.path.join(assets_base_path, "opencv_debug", f"loop{loop_num}_content_roi.png") # 修改保存路径
    )
    if not full_content_pil: print("错误 (Analyzer): 未能截取内容ROI。"); return None

    analysis_result["full_content_roi_pil_image"] = full_content_pil
    analysis_result["task_tracker_content_roi_tuple"] = content_roi_tuple

    # 3. OCR第一行识别任务类型
    print("DEBUG (Analyzer): 开始OCR第一行任务类型...")
    first_line_crop_upper = ocr_gap
    first_line_crop_lower = ocr_gap + ocr_line_h
    # ... (裁剪 first_line_pil 的安全检查逻辑，同 main.py) ...
    if first_line_crop_upper < 0: first_line_crop_upper = 0
    if first_line_crop_lower > full_content_pil.height: first_line_crop_lower = full_content_pil.height

    first_line_pil = None
    if first_line_crop_upper < first_line_crop_lower and 0 < full_content_pil.width :
        final_first_line_crop_box = (0, first_line_crop_upper, full_content_pil.width, first_line_crop_lower)
        first_line_pil = full_content_pil.crop(final_first_line_crop_box)

    if not (first_line_pil and first_line_pil.size[0]>0 and first_line_pil.size[1]>0):
        print("错误 (Analyzer): 第一行图像裁剪无效。"); return None

    ocr_task_type_text = ocr_image_region(
        first_line_pil, psm=ocr_psm_first, scale_factor=ocr_scale, preprocess=True,
        assets_base_path=assets_base_path, loop_num=loop_num, image_suffix=f"type_L{loop_num}"
    )
    print(f"DEBUG (Analyzer): OCR任务类型结果 (PSM {ocr_psm_first}): '{ocr_task_type_text}'")

    clean_raw = ocr_task_type_text.replace(' ', '').replace('\n', '').replace('"', '').replace('“', '')
    clean_bracket = clean_raw.replace('[江湖历练企务]', '').replace('[江湖历练任务]', '')
    clean_chinese_only = "".join(re.findall(r'[\u4e00-\u9fff]+', clean_bracket))
    print(f"DEBUG (Analyzer): 清理后OCR(任务类型): '{clean_chinese_only}'")

    found_task_name = None
    if target_task_keywords_map:
        for C_name, kw_list in target_task_keywords_map.items():
            for kw in kw_list:
                if kw in clean_chinese_only or kw in clean_raw: # 匹配清理后或原始清理的
                    found_task_name = C_name; break
            if found_task_name: break

    if not found_task_name: print("错误 (Analyzer): 未能识别任务类型。"); return None # 直接返回None，让主循环处理
    analysis_result["found_task_name"] = found_task_name
    print(f"DEBUG (Analyzer): 识别到任务类型: '{found_task_name}'!")

    # 4. 如果需要，OCR完整描述 (例如 "急人所急" 需要)
    ocr_full_desc = ocr_task_type_text # 默认用第一行的结果
    if found_task_name == "急人所急": # 或者其他需要完整描述的任务
        print("DEBUG (Analyzer): 为 '{found_task_name}' OCR完整描述...")
        ocr_full_desc = ocr_image_region(
            full_content_pil, psm=ocr_psm_full, scale_factor=ocr_scale, preprocess=True,
            assets_base_path=assets_base_path, loop_num=loop_num, image_suffix=f"fulldesc_L{loop_num}"
        )
        print(f"DEBUG (Analyzer): OCR完整描述结果 (PSM {ocr_psm_full}): '{ocr_full_desc}'")
    analysis_result["ocr_full_description"] = ocr_full_desc

    # 5. (可选，如果任务是“见多识广”或“急人所急”这类需要导航的) 查找NPC链接
    if found_task_name in ["见多识广", "急人所急"]: # 假设这两类都需要找链接
        print(f"DEBUG (Analyzer): 为任务 '{found_task_name}' 查找NPC链接...")
        link_loc_roi = find_green_underlined_link_opencv(
            full_content_pil, hsv_lower_g, hsv_upper_g,
            assets_base_path, loop_num, f"{found_task_name}_link" # 调试图片后缀
        )
        if link_loc_roi:
            # 将ROI内的相对坐标转换为屏幕绝对坐标
            roi_origin_x = content_roi_tuple[0]
            roi_origin_y = content_roi_tuple[1]
            screen_click_x = roi_origin_x + link_loc_roi[0]
            screen_click_y = roi_origin_y + link_loc_roi[1]
            analysis_result["npc_link_screen_coords"] = (screen_click_x, screen_click_y)
            print(f"DEBUG (Analyzer): 找到链接@ROI:{link_loc_roi}, 屏幕绝对坐标:{analysis_result['npc_link_screen_coords']}")
        else:
            print(f"警告 (Analyzer): 未找到任务 '{found_task_name}' 的NPC链接。")

    return analysis_result

if __name__ == '__main__':
    print("测试 task_tracker_analyzer.py...")
    # 这个模块的测试需要一个完整的配置对象和模拟的游戏环境
    # 通常它的功能会在 main.py 中被调用和测试
    print("请通过 main.py 来测试 Task Tracker Analyzer 的功能。")