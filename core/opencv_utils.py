# 文件名: opencv_utils.py
# 位置: ring_quest_helper/core/opencv_utils.py

import cv2
import numpy as np
import os
from PIL import Image # 用于可能的图像格式转换
import traceback # 导入 traceback


def find_green_underlined_link_opencv(roi_image_pil, hsv_lower_green, hsv_upper_green, assets_base_path="assets",
                                      loop_num=0, debug_image_suffix="link"):
    try:
        roi_cv_rgb = np.array(roi_image_pil)
        if roi_cv_rgb.size == 0: print("OpenCV错误: 输入ROI图像为空。"); return None
        if len(roi_cv_rgb.shape) < 3 or roi_cv_rgb.shape[2] == 1: print(
            "OpenCV警告: 输入图像为灰度图，无法颜色查找。"); return None
        if roi_cv_rgb.shape[2] == 4: roi_cv_rgb = cv2.cvtColor(roi_cv_rgb, cv2.COLOR_RGBA2RGB)
        hsv_image = cv2.cvtColor(roi_cv_rgb, cv2.COLOR_RGB2HSV)
        green_mask = cv2.inRange(hsv_image, hsv_lower_green, hsv_upper_green)

        # 形态学操作：目标是让下划线这种细长结构更清晰，但也要避免过度连接到文字上
        # 对于细长的下划线，一个更适合的kernel可能是横向的
        kernel_underline = np.ones((1, 7), np.uint8)  # 尝试一个更长的水平kernel，连接下划线断点
        # kernel_dilate_small_vertical = np.ones((2,1), np.uint8) # 非常轻微的垂直膨胀，如果下划线是1像素高

        # 尝试1: 先用一个小的开运算去除噪点，然后专门针对横向结构膨胀
        kernel_open = np.ones((2, 2), np.uint8)
        processed_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel_open, iterations=1)
        processed_mask = cv2.dilate(processed_mask, kernel_underline, iterations=1)

        # 尝试2: 或者只进行膨胀
        # processed_mask = cv2.dilate(green_mask, kernel_underline, iterations=1)
        # processed_mask = cv2.dilate(processed_mask, kernel_dilate_small_vertical, iterations=1)

        # --- 保存调试图片 ---
        debug_output_dir = os.path.join(assets_base_path, "opencv_debug")
        if not os.path.exists(debug_output_dir): os.makedirs(debug_output_dir, exist_ok=True)
        base_filename = f"loop{loop_num}_{debug_image_suffix}"
        try:
            cv2.imwrite(os.path.join(debug_output_dir, f"{base_filename}_0_green_mask.png"), green_mask)
            cv2.imwrite(os.path.join(debug_output_dir, f"{base_filename}_1_processed_mask.png"), processed_mask)
        except Exception as e_save_dbg:
            print(f"DEBUG: 保存OpenCV调试图时出错: {e_save_dbg}")
        # ---

        contours, _ = cv2.findContours(processed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours: print("OpenCV链接查找: processed_mask中未找到轮廓。"); return None

        # 筛选“下划线”轮廓的参数
        min_underline_width = 20  # 下划线至少要有一定宽度
        max_underline_width = 200  # 下划线最大宽度 (根据你上次找到的w=197, w=158)
        min_underline_height = 1  # 下划线可以非常细 (1像素)
        max_underline_height = 7  # 下划线不会太粗 (例如最多7像素高)
        min_underline_aspect_ratio = 4.0  # 宽度至少是高度的4倍，以确保是细长形状

        underline_candidates = []
        # image_to_draw_on_for_candidates = cv2.cvtColor(np.array(roi_image_pil), cv2.COLOR_RGB2BGR) # 用于画所有候选

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # cv2.rectangle(image_to_draw_on_for_candidates, (x,y), (x+w, y+h), (0,255,0), 1) # 画出所有通过面积前的轮廓

            # 稍微放宽一点面积，因为下划线可能很小
            if cv2.contourArea(cnt) < 10 and w < min_underline_width: continue  # 过滤掉太小的噪点或太短的线

            aspect_ratio = w / h if h > 0 else 0

            if min_underline_width <= w <= max_underline_width and \
                    min_underline_height <= h <= max_underline_height and \
                    aspect_ratio >= min_underline_aspect_ratio:
                underline_candidates.append({'x': x, 'y': y, 'w': w, 'h': h, 'cx': x + w // 2, 'cy': y + h // 2})
                # print(f"DEBUG (OpenCV Underline): 找到候选下划线: x={x},y={y},w={w},h={h}, AR={aspect_ratio:.1f}")

        # try:
        #     cv2.imwrite(os.path.join(debug_output_dir, f"{base_filename}_2a_all_green_contours.png"), image_to_draw_on_for_candidates)
        # except: pass

        if not underline_candidates:
            print("OpenCV链接查找: 未找到符合下划线特征的候选轮廓。")
            return None

        print(f"DEBUG (OpenCV Underline): 找到 {len(underline_candidates)} 个候选下划线轮廓。")

        # 选择策略：NPC链接通常在任务描述的下方，我们选择Y坐标最大的那条下划线。
        # 如果同一Y坐标有多条（比如下划线断了），可以尝试合并或取最长的那条。
        # 暂时先取Y坐标最大（最靠下）的那个候选下划线。
        # 如果链接本身可能分行，且每行都有下划线，这个策略可能只取到最后一行。
        # 但你描述的NPC在第二行，所以我们应该找描述文字中相对靠下的下划线。

        # 按下划线的y坐标（底部y+h）降序排列，再按x升序
        underline_candidates.sort(key=lambda c: (c['y'] + c['h'], c['x']), reverse=True)

        best_underline = underline_candidates[0]  # 取最下面的那条（或一组中最左的）

        final_x, final_y, final_w, final_h = best_underline['x'], best_underline['y'], best_underline['w'], \
        best_underline['h']

        print(f"DEBUG (OpenCV Underline): 选择的最佳下划线候选: x={final_x},y={final_y},w={final_w},h={final_h}")

        # --- 保存最终选定下划线的调试图像 ---
        try:
            final_debug_image = cv2.cvtColor(np.array(roi_image_pil), cv2.COLOR_RGB2BGR)
            # 用蓝色粗线条画出最终选定的下划线包围框
            cv2.rectangle(final_debug_image, (final_x, final_y), (final_x + final_w, final_y + final_h), (255, 0, 0), 2)

            # 计算基于下划线的点击点：下划线中心向上移动8个像素
            # 下划线的中心X: final_x + final_w // 2
            # 下划线的中心Y: final_y + final_h // 2
            # 点击点Y: (final_y + final_h // 2) - 8
            # (或者更稳妥的是用下划线的顶边 final_y 向上移，但如果下划线本身有几像素高，取中心再上移可能更准)
            # 我们先用下划线中心点来计算，然后向上移

            click_target_x_in_roi = final_x + final_w // 2  # 点击下划线的水平中心
            click_target_y_in_roi = (final_y + final_h // 2) - 8  # 下划线中心向上移8像素

            # 确保点击点在ROI内部 (特别是Y坐标)
            if click_target_y_in_roi < 0: click_target_y_in_roi = 0

            cv2.circle(final_debug_image, (click_target_x_in_roi, click_target_y_in_roi), 3, (0, 0, 255),
                       -1)  # 红色点标记计划点击处

            cv2.imwrite(os.path.join(debug_output_dir, f"{base_filename}_3_final_underline_and_click_target.png"),
                        final_debug_image)
            print(f"DEBUG (OpenCV Link): 已保存带最终下划线框和点击目标的图像。")
        except Exception as e_save_final_debug:
            print(f"DEBUG (OpenCV Link): 保存最终调试图像时出错: {e_save_final_debug}")
        # ---

        print(
            f"OpenCV链接查找: 基于下划线计算的计划点击点 (ROI内相对坐标): ({click_target_x_in_roi},{click_target_y_in_roi})")
        return (click_target_x_in_roi, click_target_y_in_roi)

    except Exception as e_opencv:
        print(f"OpenCV处理过程中发生错误: {e_opencv}");
        traceback.print_exc();
        return None

# (模块末尾的 if __name__ == '__main__': 测试区可以保持，但里面的测试代码需要更新或移除)
if __name__ == '__main__':
    print("opencv_utils.py 被直接运行。请通过 main.py 进行实际测试。")