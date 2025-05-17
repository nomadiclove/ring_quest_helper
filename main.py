# 文件名: main.py
# 位置: ring_quest_helper/main.py

import sys
import os

# --- 【重要修改】将项目根目录添加到 sys.path ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# --- 【重要修改结束】 ---

import time
import pyautogui
import configparser
from PIL import Image
import re
import numpy as np
import pygetwindow as gw
import traceback

# 从config_loader导入所有需要的函数
from config_loader import load_config, get_config_value, load_task_keywords, load_item_keywords, \
    load_item_sourcing_rules
# 从新的core子模块导入
from core.window_handler import find_and_setup_game_window
from core.image_utils import find_image, take_screenshot
from core.ocr_utils import ocr_image_region
from core.opencv_utils import find_green_underlined_link_opencv
from core.input_simulator import click_at

# --- 尝试导入任务处理函数 ---
JIRENSUOJI_HANDLER_AVAILABLE = False
handle_jirensuoji = None
try:
    from tasks.task_急人所急 import handle_jirensuoji

    JIRENSUOJI_HANDLER_AVAILABLE = True
    print("DEBUG: 成功导入 handle_jirensuoji 函数。")
except ImportError as e_import_jrsj:
    print(f"DEBUG: 导入 handle_jirensuoji 时发生 ImportError: {e_import_jrsj}")
    traceback.print_exc()
    print("警告: '急人所急'任务相关的函数导入失败。")
except Exception as e_other_import_jrsj:
    print(f"DEBUG: 导入 handle_jirensuoji 时发生其他未知错误: {e_other_import_jrsj}")
    traceback.print_exc()
    print("警告: '急人所急'任务相关的函数导入失败。")


def run_script():
    print("脚本开始运行...")

    # 初始化配置变量，设定默认值
    config = None
    target_task_keywords_map = {}
    item_keywords_map = {}
    item_sourcing_rules = {}
    assets_base_path = 'assets/'
    default_confidence = 0.8
    game_window_title = ""

    ocr_psm_mode_first_line = 7
    ocr_psm_mode_full_desc = 3
    first_line_gap = 5
    first_line_height = 20
    ocr_scale_factor = 3

    # 这些变量将在配置加载时被正确赋值
    lower_green = np.array([50, 100, 100])  # 默认值
    upper_green = np.array([75, 255, 255])  # 默认值

    initialization_successful = False
    try:
        # --- 步骤 0: 加载配置 ---
        print("--- 步骤 0: 加载配置 ---")
        config = load_config()
        target_task_keywords_map = load_task_keywords()
        item_keywords_map = load_item_keywords()
        item_sourcing_rules = load_item_sourcing_rules()

        assets_base_path_conf = get_config_value(config, 'General', 'AssetsBasePath', fallback=assets_base_path)
        if assets_base_path_conf: assets_base_path = assets_base_path_conf

        default_confidence_str = get_config_value(config, 'General', 'DefaultConfidence',
                                                  fallback=str(default_confidence))
        try:
            default_confidence = float(default_confidence_str)
        except (ValueError, TypeError):
            print(
                f"配置警告: General.DefaultConfidence ('{default_confidence_str}') 无效，使用默认值 {default_confidence}")

        game_window_title_conf = get_config_value(config, 'Game', 'WindowTitle')
        if not game_window_title_conf:
            print("错误：配置文件中 [Game]WindowTitle 未配置或为空。脚本无法继续。")
            initialization_successful = False
        else:
            game_window_title = game_window_title_conf
            # initialization_successful 稍后在所有必要配置加载完后统一设置

        # 只有在WindowTitle有效时才继续加载其他依赖它的可选配置
        if game_window_title:
            try:
                ocr_psm_mode_first_line = int(
                    get_config_value(config, 'OCR', 'PSM_Mode_FirstLine', fallback=str(ocr_psm_mode_first_line)))
            except ValueError:
                print(f"配置警告: OCR.PSM_Mode_FirstLine 无效，使用默认值 {ocr_psm_mode_first_line}")
            try:
                ocr_psm_mode_full_desc = int(
                    get_config_value(config, 'OCR', 'PSM_Mode_FullDesc', fallback=str(ocr_psm_mode_full_desc)))
            except ValueError:
                print(f"配置警告: OCR.PSM_Mode_FullDesc 无效，使用默认值 {ocr_psm_mode_full_desc}")
            try:
                first_line_gap = int(get_config_value(config, 'OCR', 'FirstLineGap', fallback=str(first_line_gap)))
            except ValueError:
                print(f"配置警告: OCR.FirstLineGap 无效，使用默认值 {first_line_gap}")
            try:
                first_line_height = int(
                    get_config_value(config, 'OCR', 'FirstLineHeight', fallback=str(first_line_height)))
            except ValueError:
                print(f"配置警告: OCR.FirstLineHeight 无效，使用默认值 {first_line_height}")
            try:
                ocr_scale_factor = int(get_config_value(config, 'OCR', 'ScaleFactor', fallback=str(ocr_scale_factor)))
            except ValueError:
                print(f"配置警告: OCR.ScaleFactor 无效，使用默认值 {ocr_scale_factor}")

            temp_lower_green_init = lower_green.copy()  # 保存默认值以便fallback
            temp_upper_green_init = upper_green.copy()
            try:
                h_min = int(get_config_value(config, 'HSV_Green', 'H_Min', fallback=str(temp_lower_green_init[0])))
                s_min = int(get_config_value(config, 'HSV_Green', 'S_Min', fallback=str(temp_lower_green_init[1])))
                v_min = int(get_config_value(config, 'HSV_Green', 'V_Min', fallback=str(temp_lower_green_init[2])))
                h_max = int(get_config_value(config, 'HSV_Green', 'H_Max', fallback=str(temp_upper_green_init[0])))
                s_max = int(get_config_value(config, 'HSV_Green', 'S_Max', fallback=str(temp_upper_green_init[1])))
                v_max = int(get_config_value(config, 'HSV_Green', 'V_Max', fallback=str(temp_upper_green_init[2])))
                lower_green = np.array([h_min, s_min, v_min])
                upper_green = np.array([h_max, s_max, v_max])
            except ValueError:
                print(f"配置警告: HSV_Green 中的一个或多个值无效，将使用预设默认值。")
                lower_green = temp_lower_green_init  # 确保出错时仍使用默认值
                upper_green = temp_upper_green_init
            print(f"DEBUG: 使用的绿色HSV范围 - Lower: {lower_green}, Upper: {upper_green}")
            initialization_successful = True  # 如果WindowTitle有效，则认为初始化主要部分成功

        if not target_task_keywords_map: print("警告：未能加载任务关键字映射 (tasks_keywords.json)。")
        if not item_keywords_map: print("警告：未能加载物品关键字映射 (item_keywords.json)。")
        if not item_sourcing_rules: print("警告：未能加载物品获取规则 (item_sourcing_rules.json)。")

        if not JIRENSUOJI_HANDLER_AVAILABLE: print("警告: '急人所急'处理函数在初始化时未能成功导入。")

    except FileNotFoundError as e_init_file:
        print(
            f"初始化错误（配置文件等找不到）：{e_init_file.filename if hasattr(e_init_file, 'filename') else e_init_file}")
        initialization_successful = False
    except configparser.Error as e_cfg_init:
        print(f"配置文件读取错误 (初始化阶段): {e_cfg_init}");
        traceback.print_exc()
        initialization_successful = False
    except Exception as e_init:
        print(f"脚本初始化时发生未预料的错误: {e_init}");
        traceback.print_exc()
        initialization_successful = False

    if not initialization_successful:
        print("脚本初始化失败，程序即将退出。")
        print("脚本运行结束.")
        return

    loop_count = 0
    max_loops_str = get_config_value(config, 'General', 'MaxLoops', fallback='5')
    try:
        max_loops = int(max_loops_str)
    except ValueError:
        max_loops = 5; print(f"配置警告: [General]MaxLoops 值 '{max_loops_str}' 无效，使用默认值 5。")
    if max_loops <= 0: print("MaxLoops <= 0，脚本将无限循环 (按Ctrl+C停止)。")

    main_loop_active = True
    try:  # 这个最外层的 try 对应最后的 finally
        while main_loop_active:
            try:  # 这个 try...except 用于捕获单次循环迭代中的错误
                loop_count += 1
                print(f"\n===== 开始第 {loop_count} 次任务循环 =====")
                if max_loops > 0 and loop_count > max_loops:
                    print(f"已达到最大循环次数 {max_loops}，准备结束主循环。");
                    main_loop_active = False;
                    continue

                game_screen_region = find_and_setup_game_window(game_window_title)
                if not game_screen_region: print("错误：未能定位到游戏窗口/区域。等待10秒后重试..."); time.sleep(
                    10); continue

                print("\n--- 阶段1: 查找任务追踪标头 ---")
                header_img_name = get_config_value(config, 'UI_Anchors', 'TaskTrackerHeader')
                if not header_img_name: print("错误：TaskTrackerHeader未配置。"); time.sleep(5); continue
                header_img_path = os.path.join(assets_base_path, header_img_name)
                time.sleep(0.5);
                header_loc = find_image(header_img_path, confidence=default_confidence, region=game_screen_region)
                if not header_loc: print(f"未能找到“任务追踪标头”。等待5秒..."); time.sleep(5); continue
                print(f"成功找到“任务追踪标头”，中心点: ({header_loc.x}, {header_loc.y})")

                print("\n--- 阶段2: 计算内容ROI并截图 ---")
                bar_w, bar_h, content_h = 230, 22, 100
                roi_tl_x = header_loc.x - bar_w // 2
                roi_tl_y = header_loc.y - bar_h // 2 + bar_h
                content_roi_tuple = (int(roi_tl_x), int(roi_tl_y), int(bar_w), int(content_h))
                print(f"推断出的内容ROI: {content_roi_tuple}")
                full_content_pil = take_screenshot(region=content_roi_tuple)
                if not full_content_pil: print("错误：未能截取内容ROI。尝试下一次..."); time.sleep(5); continue

                print("\n--- 阶段3: OCR识别任务类型 ---")
                first_line_crop_upper = first_line_gap
                first_line_crop_lower = first_line_gap  + first_line_height
                if first_line_crop_upper < 0: first_line_crop_upper = 0
                if first_line_crop_lower > full_content_pil.height: first_line_crop_lower = full_content_pil.height

                first_line_pil = None
                if first_line_crop_upper < first_line_crop_lower and 0 < full_content_pil.width:
                    final_first_line_crop_box = (
                    0, first_line_crop_upper, full_content_pil.width, first_line_crop_lower)
                    first_line_pil = full_content_pil.crop(final_first_line_crop_box)

                if not (first_line_pil and first_line_pil.size[0] > 0 and first_line_pil.size[1] > 0):
                    print("错误：第一行图像裁剪无效。等待5秒...");
                    time.sleep(5);
                    continue

                ocr_task_type_text = ocr_image_region(
                    first_line_pil, psm=ocr_psm_mode_first_line, scale_factor=ocr_scale_factor, preprocess=True,
                    assets_base_path=assets_base_path, loop_num=loop_count, image_suffix=f"type_L{loop_count}"
                )
                print(f"OCR结果(第一行, PSM {ocr_psm_mode_first_line}, 进行了预处理): '{ocr_task_type_text}'")

                clean_raw = ocr_task_type_text.replace(' ', '').replace('\n', '').replace('"', '').replace('“', '')
                clean_bracket = clean_raw.replace('[江湖历练企务]', '').replace('[江湖历练任务]', '')
                clean_chinese_only = "".join(re.findall(r'[\u4e00-\u9fff]+', clean_bracket))
                print(f"清理后OCR(任务类型): '{clean_chinese_only}'")

                found_task_name = None
                if target_task_keywords_map:
                    for C_name, kw_list in target_task_keywords_map.items():
                        for kw in kw_list:
                            if kw in clean_chinese_only or kw in clean_raw:
                                found_task_name = C_name;
                                break
                        if found_task_name: break

                if not found_task_name: print(f"未能识别任务类型。等待5秒..."); time.sleep(5); continue
                print(f"识别到任务类型: '{found_task_name}'!")

                ocr_full_description = ""
                if found_task_name == "急人所急":
                    print(f"DEBUG: 为'{found_task_name}'OCR完整描述...")  # 使用 f-string
                    ocr_full_description = ocr_image_region(
                        full_content_pil, psm=ocr_psm_mode_full_desc, scale_factor=ocr_scale_factor, preprocess=True,
                        assets_base_path=assets_base_path, loop_num=loop_count, image_suffix=f"fulldesc_L{loop_count}"
                    )
                    print(f"OCR完整描述结果 (PSM {ocr_psm_mode_full_desc}): '{ocr_full_description}'")
                else:
                    ocr_full_description = ocr_task_type_text

                script_vars = {
                    "config": config, "assets_base_path": assets_base_path,
                    "full_content_roi_pil_image": full_content_pil,
                    "task_tracker_content_roi_tuple": content_roi_tuple,
                    "item_keywords_map": item_keywords_map,
                    "item_sourcing_rules": item_sourcing_rules,
                    "ocr_full_description_text": ocr_full_description,
                    "lower_green": lower_green,  # 使用在函数顶部定义的 lower_green
                    "upper_green": upper_green,  # 使用在函数顶部定义的 upper_green
                    "wait_after_click_seconds": int(
                        get_config_value(config, 'General', 'WaitAfterAction', fallback='15')),  # 从配置读取或用默认
                    "default_confidence": default_confidence, "loop_count": loop_count,
                }
                task_handled_successfully = False

                if found_task_name == "见多识广":
                    print(f"\n--- 处理任务: {found_task_name} ---")
                    link_loc_roi = find_green_underlined_link_opencv(
                        full_content_pil, lower_green, upper_green,  # 使用正确的HSV变量
                        assets_base_path, loop_count, f"{found_task_name}_link"
                    )
                    if link_loc_roi:
                        click_x = content_roi_tuple[0] + link_loc_roi[0]
                        click_y = content_roi_tuple[1] + link_loc_roi[1]
                        print(f"找到链接@ROI:{link_loc_roi}, 屏幕:{click_x, click_y}")
                        click_at(click_x, click_y)
                        print("已点击链接。")
                        task_handled_successfully = True
                    else:
                        print(f"未找到链接({found_task_name})。")

                elif found_task_name == "急人所急":
                    print(f"\n--- 处理任务: {found_task_name} ---")
                    if JIRENSUOJI_HANDLER_AVAILABLE and handle_jirensuoji:
                        task_handled_successfully = handle_jirensuoji(script_vars)
                    else:
                        print(f"处理函数 handle_jirensuoji 未导入。跳过。")
                        task_handled_successfully = True
                else:
                    print(f"任务类型 '{found_task_name}' 处理逻辑未实现。")
                    task_handled_successfully = True

                if task_handled_successfully:
                    wait_duration = script_vars.get('wait_after_click_seconds', 15)
                    print(f"任务处理完毕/派发，等待 {wait_duration} 秒...");
                    time.sleep(wait_duration)
                else:
                    print(f"任务 '{found_task_name}' 未成功处理。等待5秒...");
                    time.sleep(5)

            except KeyboardInterrupt:
                print("循环被中断。");
                main_loop_active = False
            except Exception as e_loop:
                print(f"循环中错误: {e_loop}");
                traceback.print_exc();
                time.sleep(10)

            if main_loop_active: time.sleep(1)

    except KeyboardInterrupt:
        print("主流程被中断。")
    except Exception as e_outer:
        print(f"主流程致命错误: {e_outer}");
        traceback.print_exc()
    finally:
        print("脚本运行结束。")


if __name__ == '__main__':
    run_script()