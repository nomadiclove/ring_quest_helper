# tasks/jianduoshiguang_processor.py
import cv2
import os
import pyautogui # 仅用于可能的延时

# 从core和game_elements导入我们需要的函数
from core.image_matcher import find_template_in_image
from core.color_filter import find_contours_by_bgr_range
from core.text_recognizer import recognize_text
# input_simulator 会作为参数传入，config也是
from game_elements.task_panel_analyzer import get_relative_roi_from_layout

def process_jianduoshiguang(
    main_game_image_bgr,
    game_screen_abs_rect,
    config, # 已加载的 ConfigParser 对象
    input_sim # input_simulator 模块
    ):
    """
    处理"见多识广"类型任务的逻辑。
    返回状态字符串。
    """
    print("DEBUG (proc): 进入 process_jianduoshiguang")

    # --- 0. 获取必要的配置和项目根路径 ---
    # 假设 config 对象中已经由 main.py 设置了 'paths'/'projectroot'
    # 如果没有，则尝试从当前文件路径推断 (这在 tasks/ 目录下可能不准，最好由main.py传入)
    project_root = config.get("paths", "projectroot", 
                              fallback=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"DEBUG (proc): Project root: {project_root}")

    # --- 1. 定位 "任务追踪" 锚点 ---
    print("DEBUG (proc): 开始读取任务追踪模板配置...")
    header_template_rel_path = config.get('tasktrackerui_templates', 'headertemplatepath') # 相对于项目根目录
    header_template_path = os.path.join(project_root, header_template_rel_path)
    header_match_threshold = config.getfloat('tasktrackerui_templates', 'headermatchthreshold')
    print(f"DEBUG (proc): 模板路径: {header_template_path}, 阈值: {header_match_threshold}")

    header_match = find_template_in_image(main_game_image_bgr, header_template_path, header_match_threshold)
    if not header_match:
        print("DEBUG (proc): 未能找到 '任务追踪' 模板。")
        return "template_not_found_in_processor"
    header_x, header_y, header_w, header_h, _ = header_match
    print(f"DEBUG (proc): '任务追踪' 模板找到: X={header_x}, Y={header_y}, W={header_w}, H={header_h}")

    # --- 2. 获取UI布局配置、关键词配置、颜色范围、OCR参数 ---
    print("DEBUG (proc): 开始读取UI布局、关键词、颜色和OCR配置...")
    ui_layout_config = dict(config.items('tasktrackerui_layout'))

    jdg_keywords_str = config.get('taskkeywords', 'jianduoshiguang')
    jdg_keywords = [kw.strip() for kw in jdg_keywords_str.split(',') if kw.strip()]

    target_npc_name_normalized = config.get('jianduoshiguang_npc_keywords', 'targetnpcname')
    npc_keywords_str = config.get('jianduoshiguang_npc_keywords', 'keywords')
    npc_keywords = [kw.strip() for kw in npc_keywords_str.split(',') if kw.strip()]

    green_lower_str = config.get('tasktrackerui_layout', 'npcnamegreenlowerbound')
    green_lower = tuple(map(int, green_lower_str.split(',')))
    green_upper_str = config.get('tasktrackerui_layout', 'npcnamegreenupperbound')
    green_upper = tuple(map(int, green_upper_str.split(',')))

    task_type_psm = config.getint('ocr_params', 'tasktypepsm')
    npc_name_psm = config.getint('ocr_params', 'npcnamersm')
    ocr_upscale = config.getfloat('ocr_params', 'defaultupscalefactor')
    print("DEBUG (proc): 所有特定配置项读取完毕。")

    # --- 3. 计算并识别 "任务类型" ---
    task_type_roi_coords = get_relative_roi_from_layout(ui_layout_config, 'tasktype', header_x, header_y)
    if not task_type_roi_coords: 
        print("DEBUG (proc): 计算任务类型ROI失败 (get_relative_roi_from_layout 返回 None)")
        return "config_error_tasktype_roi"

    tt_x, tt_y, tt_w, tt_h = task_type_roi_coords
    if not (tt_x >= 0 and tt_y >= 0 and tt_x + tt_w <= main_game_image_bgr.shape[1] and tt_y + tt_h <= main_game_image_bgr.shape[0]):
        print(f"DEBUG (proc): 任务类型ROI ({tt_x},{tt_y},{tt_w},{tt_h}) 超出截图范围 ({main_game_image_bgr.shape[1]}x{main_game_image_bgr.shape[0]})")
        return "roi_out_of_bounds_tasktype"

    task_type_img_bgr = main_game_image_bgr[tt_y : tt_y + tt_h, tt_x : tt_x + tt_w]
    # cv2.imwrite(os.path.join(project_root, "debug_task_type_roi_from_task.png"), task_type_img_bgr)

    recognized_task_type = recognize_text(task_type_img_bgr, lang='chi_sim', psm=task_type_psm, upscale_factor=ocr_upscale)
    if not recognized_task_type: 
        print("DEBUG (proc): OCR未能识别出任务类型文本。")
        return "ocr_failed_tasktype"
    print(f"DEBUG (proc): 识别出的任务类型文本: '{recognized_task_type}'")

    is_target_task = False
    for keyword in jdg_keywords:
        if keyword in recognized_task_type:
            is_target_task = True
            break
    if not is_target_task:
        print(f"DEBUG (proc): 识别的任务类型 '{recognized_task_type}' 与关键词不匹配。")
        return "task_type_mismatch"
    print("DEBUG (proc): 任务类型匹配成功!")

    # --- 4. 计算并获取 "任务描述" ROI ---
    task_desc_roi_coords = get_relative_roi_from_layout(ui_layout_config, 'taskdesc', header_x, header_y)
    if not task_desc_roi_coords: 
        print("DEBUG (proc): 计算任务描述ROI失败 (get_relative_roi_from_layout 返回 None)")
        return "config_error_taskdesc_roi"

    td_x, td_y, td_w, td_h = task_desc_roi_coords
    if not (td_x >= 0 and td_y >= 0 and td_x + td_w <= main_game_image_bgr.shape[1] and td_y + td_h <= main_game_image_bgr.shape[0]):
        print(f"DEBUG (proc): 任务描述ROI ({td_x},{td_y},{td_w},{td_h}) 超出截图范围。")
        return "roi_out_of_bounds_taskdesc"

    task_desc_img_bgr = main_game_image_bgr[td_y : td_y + td_h, td_x : td_x + td_w]
    cv2.imwrite(os.path.join(project_root, "debug_task_desc_roi_from_task.png"), task_desc_img_bgr) # 保留这个，重要
    print("DEBUG (proc): 任务描述ROI已切割并保存。")

    # --- 5. 在 "任务描述" ROI 中查找绿色NPC名字 ---
    print(f"DEBUG (proc): 开始在任务描述ROI中查找绿色块，颜色范围 L:{green_lower} U:{green_upper}")
    green_blobs = find_contours_by_bgr_range(task_desc_img_bgr, green_lower, green_upper, min_contour_area=5) # 使用较小min_area

    if not green_blobs: 
        print("DEBUG (proc): 未在任务描述ROI中找到任何绿色块。")
        return "npc_not_found_color"

    print(f"DEBUG (proc): 找到 {len(green_blobs)} 个潜在的绿色块。")
    found_npc_to_click = False
    task_desc_roi_with_boxes_drawn = task_desc_img_bgr.copy() # 用于画框

    for i, (gx, gy, gw, gh) in enumerate(green_blobs):
        print(f"DEBUG (proc):  处理绿色块 {i+1}: X={gx}, Y={gy}, W={gw}, H={gh}")
        cv2.rectangle(task_desc_roi_with_boxes_drawn, (gx, gy), (gx + gw, gy + gh), (0, 0, 255), 1)

        ocr_gy_end = min(gy + gh, task_desc_img_bgr.shape[0])
        ocr_gx_end = min(gx + gw, task_desc_img_bgr.shape[1])
        if gy >= ocr_gy_end or gx >= ocr_gx_end : 
            print(f"DEBUG (proc):    绿色块 {i+1} 边界无效，跳过OCR。")
            continue

        green_blob_for_ocr = task_desc_img_bgr[gy:ocr_gy_end, gx:ocr_gx_end]
        # cv2.imwrite(os.path.join(project_root, f"debug_npc_blob_{i+1}.png"), green_blob_for_ocr)

        npc_text = recognize_text(green_blob_for_ocr, lang='chi_sim', psm=npc_name_psm, upscale_factor=ocr_upscale)
        if not npc_text: 
            print(f"DEBUG (proc):    绿色块 {i+1} OCR未能识别出文本。")
            continue
        print(f"DEBUG (proc):    绿色块 {i+1} OCR结果: '{npc_text}'")

        for npc_keyword in npc_keywords:
            if npc_keyword in npc_text:
                print(f"DEBUG (proc):    匹配到NPC关键词 '{npc_keyword}' in '{npc_text}'!")
                click_x_game_relative = td_x + gx + gw // 2
                click_y_game_relative = td_y + gy + gh // 2

                abs_screen_x = game_screen_abs_rect[0] + click_x_game_relative
                abs_screen_y = game_screen_abs_rect[1] + click_y_game_relative

                print(f"DEBUG (proc):    准备点击NPC '{target_npc_name_normalized}' 在游戏内({click_x_game_relative},{click_y_game_relative}), 屏幕({abs_screen_x},{abs_screen_y})")
                # input_sim.click_screen_coords(abs_screen_x, abs_screen_y) # 实际点击先注释
                print("DEBUG (proc):    (模拟点击已注释)") 
                found_npc_to_click = True
                break 
        if found_npc_to_click:
            break 

    cv2.imwrite(os.path.join(project_root, "debug_task_desc_with_green_blobs.png"), task_desc_roi_with_boxes_drawn) # 保存画了框的图
    print("DEBUG (proc): 任务描述ROI (可能带有绿色块标记) 已保存。")

    return "npc_clicked" if found_npc_to_click else "npc_not_found_ocr"