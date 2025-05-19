# tasks/jianduoshiguang_processor.py
import cv2
import os
import pyautogui 

from core.image_matcher import find_template_in_image
from core.color_filter import find_contours_by_bgr_range
from core.text_recognizer import recognize_text_with_paddle # 使用PaddleOCR
from game_elements.task_panel_analyzer import get_relative_roi_from_layout

def process_jianduoshiguang(
    main_game_image_bgr,
    game_screen_abs_rect,
    config, 
    input_sim 
    ):
    print("DEBUG (proc): Entering process_jianduoshiguang")

    project_root = config.get("paths", "projectroot")
    # print(f"DEBUG (proc): Project root: {project_root}") # 可以按需开启

    print("DEBUG (proc): Reading task tracker template config...")
    header_template_rel_path = config.get('tasktrackerui_templates', 'headertemplatepath')
    header_template_path = os.path.join(project_root, header_template_rel_path)
    header_match_threshold = config.getfloat('tasktrackerui_templates', 'headermatchthreshold')
    # print(f"DEBUG (proc): Template path: {header_template_path}, Threshold: {header_match_threshold}")

    header_match = find_template_in_image(main_game_image_bgr, header_template_path, header_match_threshold)
    if not header_match:
        print("DEBUG (proc): Failed to find 'Task Tracker' template.")
        return "template_not_found_in_processor"
    header_x, header_y, header_w, header_h, _ = header_match
    print(f"DEBUG (proc): 'Task Tracker' template found: X={header_x}, Y={header_y}, W={header_w}, H={header_h}")

    print("DEBUG (proc): Reading UI layout and keyword configs...")
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
    # print("DEBUG (proc): All specific configs read.") # 可以按需开启

    task_type_roi_coords = get_relative_roi_from_layout(ui_layout_config, 'tasktype', header_x, header_y)
    if not task_type_roi_coords: 
        print("DEBUG (proc): Failed to calculate TaskType ROI.")
        return "config_error_tasktype_roi"

    tt_x, tt_y, tt_w, tt_h = task_type_roi_coords
    if not (tt_x >= 0 and tt_y >= 0 and tt_x + tt_w <= main_game_image_bgr.shape[1] and tt_y + tt_h <= main_game_image_bgr.shape[0]):
        print(f"DEBUG (proc): TaskType ROI out of bounds.")
        return "roi_out_of_bounds_tasktype"

    task_type_img_bgr = main_game_image_bgr[tt_y : tt_y + tt_h, tt_x : tt_x + tt_w]
    # cv2.imwrite(os.path.join(project_root, "debug_task_type_roi_from_task.png"), task_type_img_bgr)

    recognized_task_type = recognize_text_with_paddle(task_type_img_bgr) 
    if not recognized_task_type: 
        print("DEBUG (proc): PaddleOCR failed to recognize TaskType text.")
        return "ocr_failed_tasktype"
    print(f"DEBUG (proc): Recognized TaskType text (PaddleOCR): '{recognized_task_type}'")

    is_target_task = any(keyword in recognized_task_type for keyword in jdg_keywords if keyword)
    if not is_target_task:
        print(f"DEBUG (proc): Recognized TaskType '{recognized_task_type}' does not match keywords.")
        return "task_type_mismatch"
    print("DEBUG (proc): TaskType matched!")

    task_desc_roi_coords = get_relative_roi_from_layout(ui_layout_config, 'taskdesc', header_x, header_y)
    if not task_desc_roi_coords: 
        print("DEBUG (proc): Failed to calculate TaskDesc ROI.")
        return "config_error_taskdesc_roi"

    td_x, td_y, td_w, td_h = task_desc_roi_coords
    if not (td_x >= 0 and td_y >= 0 and td_x + td_w <= main_game_image_bgr.shape[1] and td_y + td_h <= main_game_image_bgr.shape[0]):
        print(f"DEBUG (proc): TaskDesc ROI out of bounds.")
        return "roi_out_of_bounds_taskdesc"

    task_desc_img_bgr = main_game_image_bgr[td_y : td_y + td_h, td_x : td_x + td_w]
    # cv2.imwrite(os.path.join(project_root, "debug_task_desc_roi_from_task.png"), task_desc_img_bgr)
    # print("DEBUG (proc): TaskDesc ROI cut and saved.")

    print(f"DEBUG (proc): Finding green blobs in TaskDesc ROI. Color range L:{green_lower} U:{green_upper}")
    green_blobs = find_contours_by_bgr_range(task_desc_img_bgr, green_lower, green_upper, min_contour_area=1) 

    if not green_blobs: 
        print("DEBUG (proc): No green blobs found in TaskDesc ROI.")
        return "npc_not_found_color"

    print(f"DEBUG (proc): Found {len(green_blobs)} potential green blob(s).")
    found_npc_to_click = False
    task_desc_roi_with_boxes_drawn = task_desc_img_bgr.copy()

    for i, (gx, gy, gw, gh) in enumerate(green_blobs):
        # print(f"DEBUG (proc):  Processing green blob {i+1}: X={gx}, Y={gy}, W={gw}, H={gh}") # 可以按需开启
        cv2.rectangle(task_desc_roi_with_boxes_drawn, (gx, gy), (gx + gw, gy + gh), (0, 0, 255), 1)

        ocr_gy_end = min(gy + gh, task_desc_img_bgr.shape[0])
        ocr_gx_end = min(gx + gw, task_desc_img_bgr.shape[1])
        if gy >= ocr_gy_end or gx >= ocr_gx_end : 
            # print(f"DEBUG (proc):    Green blob {i+1} has invalid bounds, skipping OCR.") # 可以按需开启
            continue

        green_blob_for_ocr = task_desc_img_bgr[gy:ocr_gy_end, gx:ocr_gx_end]
        # cv2.imwrite(os.path.join(project_root, f"debug_npc_blob_ocr_input_{i+1}.png"), green_blob_for_ocr) # 保存送入OCR的小块

        npc_text = recognize_text_with_paddle(green_blob_for_ocr) 
        if not npc_text: 
            # print(f"DEBUG (proc):    Green blob {i+1} OCR (Paddle) failed to recognize text.") # 可以按需开启
            continue
        print(f"DEBUG (proc):    Green blob {i+1} OCR (Paddle) result: '{npc_text}'")

        for npc_keyword in npc_keywords:
            if npc_keyword and npc_keyword in npc_text:
                print(f"DEBUG (proc):    Matched NPC keyword '{npc_keyword}' in '{npc_text}'!")
                click_x_game_relative = td_x + gx + gw // 2
                click_y_game_relative = td_y + gy + gh // 2

                abs_screen_x = game_screen_abs_rect[0] + click_x_game_relative
                abs_screen_y = game_screen_abs_rect[1] + click_y_game_relative

                print(f"DEBUG (proc):    Preparing to click NPC '{target_npc_name_normalized}' at game_rel({click_x_game_relative},{click_y_game_relative}), screen_abs({abs_screen_x},{abs_screen_y})")
                # input_sim.click_screen_coords(abs_screen_x, abs_screen_y) 
                print("DEBUG (proc):    (Simulated click is commented out)") 
                found_npc_to_click = True
                break 
        if found_npc_to_click:
            break 

    # cv2.imwrite(os.path.join(project_root, "debug_task_desc_with_green_blobs.png"), task_desc_roi_with_boxes_drawn)
    # print("DEBUG (proc): TaskDesc ROI (with potential green blob boxes) saved.") # 可以按需开启

    return "npc_clicked" if found_npc_to_click else "npc_not_found_ocr"