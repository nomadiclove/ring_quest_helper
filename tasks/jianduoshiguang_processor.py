import cv2
import os # 用于路径操作
import pyautogui # 仅用于可能的延时，或直接调用其点击（如果不用input_simulator）

# 从core和game_elements导入我们需要的函数
# 注意这里的相对导入路径，假设tasks和core, game_elements是同级或可访问
# 如果直接运行此文件进行测试，可能需要调整sys.path或使用绝对导入（如果项目已安装）
# 为了在main.py中调用方便，我们使用项目根目录的导入方式
from core.image_matcher import find_template_in_image
from core.color_filter import find_contours_by_bgr_range
from core.text_recognizer import recognize_text
from core.input_simulator import click_screen_coords # 假设我们用这个点击
from game_elements.task_panel_analyzer import get_relative_roi_from_layout
# config_loader 会由调用者传入加载好的config对象

def process_jianduoshiguang(
    main_game_image_bgr,      # 1366x768的游戏画面截图 (BGR NumPy array)
    game_screen_abs_rect,     # 1366x768游戏画面在屏幕上的绝对矩形 (x, y, w, h)
    config,                   # 已加载的ConfigParser对象
    input_sim,                # InputSimulator的实例 (如果封装成了类) 或模块本身
    # window_manager          # WindowManager的实例 (如果需要激活等操作)
    # 我们可以直接传入 game_screen_abs_rect[0] 和 game_screen_abs_rect[1] 作为点击的基准
    ):
    """
    处理"见多识广"类型任务的逻辑。

    返回:
    - str: "npc_clicked", "npc_not_found", "task_type_mismatch", "template_not_found", "config_error"
    """

    # --- 1. 定位 "任务追踪" 锚点 ---
    # 模板路径需要从配置或固定路径获取
    # 假设项目根目录是 main.py 所在的目录
    try:
        project_root = config.get("Paths", "ProjectRoot", fallback=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    except Exception: # 如果Paths或ProjectRoot不存在，使用默认计算
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # tasks -> project_root

    header_template_path = os.path.join(project_root, 
                                        config.get('TaskTrackerUI_Templates', 'HeaderTemplatePath', 
                                                   fallback='assets/templates/task_tracker_header.png'))

    header_match_threshold = config.getfloat('TaskTrackerUI_Templates', 'HeaderMatchThreshold', fallback=0.7)

    header_match = find_template_in_image(main_game_image_bgr, header_template_path, header_match_threshold)
    if not header_match:
        return "template_not_found"
    header_x, header_y, _, _ , _ = header_match # 我们只需要左上角作为锚点

    # --- 2. 获取UI布局配置和关键词配置 ---
    try:
        ui_layout_config = dict(config.items('TaskTrackerUI_Layout'))
        # 任务类型关键词
        jdg_keywords_str = config.get('TaskKeywords', 'JianDuoShiGuang', fallback="")
        jdg_keywords = [kw.strip() for kw in jdg_keywords_str.split(',') if kw.strip()]
        # NPC名字关键词 (例如 "灵儿")
        target_npc_name_normalized = config.get('JianDuoShiGuang_NPC', 'TargetNPCName', fallback="灵儿") # 规范名
        npc_keywords_str = config.get('JianDuoShiGuang_NPC', 'Keywords', fallback="灵儿,灵L,去儿")
        npc_keywords = [kw.strip() for kw in npc_keywords_str.split(',') if kw.strip()]
        # 绿色范围
        green_lower = tuple(map(int, config.get('TaskTrackerUI_Layout', 'NpcNameGreenLowerBound').split(',')))
        green_upper = tuple(map(int, config.get('TaskTrackerUI_Layout', 'NpcNameGreenUpperBound').split(',')))
        # OCR参数 (可以从配置读取，或在此处硬编码)
        task_type_psm = config.getint('OCR_Params', 'TaskTypePSM', fallback=7)
        npc_name_psm = config.getint('OCR_Params', 'NpcNamePSM', fallback=8)
        ocr_upscale = config.getfloat('OCR_Params', 'DefaultUpscaleFactor', fallback=1.0)

    except Exception: # 捕获所有配置读取错误
        # import traceback; traceback.print_exc() # DEBUG
        return "config_error"

    # --- 3. 计算并识别 "任务类型" ---
    task_type_roi_coords = get_relative_roi_from_layout(ui_layout_config, 'TaskType', header_x, header_y)
    if not task_type_roi_coords: return "config_error"

    tt_x, tt_y, tt_w, tt_h = task_type_roi_coords
    # 确保ROI在图像内
    if not (tt_x >= 0 and tt_y >= 0 and tt_x + tt_w <= main_game_image_bgr.shape[1] and tt_y + tt_h <= main_game_image_bgr.shape[0]):
        return "roi_out_of_bounds_tasktype"

    task_type_img_bgr = main_game_image_bgr[tt_y : tt_y + tt_h, tt_x : tt_x + tt_w]
    # cv2.imwrite(os.path.join(project_root, "debug_task_type_roi_from_task.png"), task_type_img_bgr) # DEBUG

    recognized_task_type = recognize_text(task_type_img_bgr, lang='chi_sim', psm=task_type_psm, upscale_factor=ocr_upscale) # 可以加入预处理参数

    if not recognized_task_type: return "ocr_failed_tasktype"

    is_target_task = False
    for keyword in jdg_keywords:
        if keyword in recognized_task_type:
            is_target_task = True
            break
    if not is_target_task:
        return "task_type_mismatch"

    # --- 4. 计算并获取 "任务描述" ROI ---
    task_desc_roi_coords = get_relative_roi_from_layout(ui_layout_config, 'TaskDesc', header_x, header_y)
    if not task_desc_roi_coords: return "config_error"

    td_x, td_y, td_w, td_h = task_desc_roi_coords
    if not (td_x >= 0 and td_y >= 0 and td_x + td_w <= main_game_image_bgr.shape[1] and td_y + td_h <= main_game_image_bgr.shape[0]):
        return "roi_out_of_bounds_taskdesc"

    task_desc_img_bgr = main_game_image_bgr[td_y : td_y + td_h, td_x : td_x + td_w]
    # cv2.imwrite(os.path.join(project_root, "debug_task_desc_roi_from_task.png"), task_desc_img_bgr) # DEBUG

    # --- 5. 在 "任务描述" ROI 中查找绿色NPC名字 ---
    green_blobs = find_contours_by_bgr_range(task_desc_img_bgr, green_lower, green_upper, min_contour_area=5)

    if not green_blobs: return "npc_not_found_color" # 未找到绿色块

    found_npc_to_click = False
    for gx, gy, gw, gh in green_blobs:
        # 从原始任务描述ROI中切割绿色块用于OCR (避免用膨胀后的)
        ocr_gy_end = min(gy + gh, task_desc_img_bgr.shape[0])
        ocr_gx_end = min(gx + gw, task_desc_img_bgr.shape[1])
        if gy >= ocr_gy_end or gx >= ocr_gx_end : continue # 无效块

        green_blob_for_ocr = task_desc_img_bgr[gy:ocr_gy_end, gx:ocr_gx_end]
        # cv2.imwrite(os.path.join(project_root, f"debug_npc_blob_{gx}_{gy}.png"), green_blob_for_ocr) # DEBUG

        npc_text = recognize_text(green_blob_for_ocr, lang='chi_sim', psm=npc_name_psm, upscale_factor=ocr_upscale) # 可以加入预处理参数
        if not npc_text: continue

        for npc_keyword in npc_keywords:
            if npc_keyword in npc_text:
                # 找到了目标NPC！
                # 计算点击坐标 (中心点，相对于1366x768游戏画面)
                click_x_game_relative = td_x + gx + gw // 2
                click_y_game_relative = td_y + gy + gh // 2

                # 转换为屏幕绝对坐标
                abs_screen_x = game_screen_abs_rect[0] + click_x_game_relative
                abs_screen_y = game_screen_abs_rect[1] + click_y_game_relative

                # 调用点击 (使用传入的 input_sim 模块或实例)
                input_sim.click_screen_coords(abs_screen_x, abs_screen_y)
                # print(f"点击NPC '{target_npc_name_normalized}' 在游戏内 ({click_x_game_relative},{click_y_game_relative}), 屏幕 ({abs_screen_x},{abs_screen_y})") # DEBUG
                found_npc_to_click = True
                break # 点击一个后就跳出内层循环
        if found_npc_to_click:
            break # 跳出外层循环 (green_blobs)

    return "npc_clicked" if found_npc_to_click else "npc_not_found_ocr"