import cv2
import numpy as np
import os

def find_template(screen_image_data, template_image_path, threshold=0.8):
    """
    在给定的屏幕图像数据中查找模板图片。

    参数:
    - screen_image_data (numpy.ndarray): BGR格式的屏幕截图数据。
    - template_image_path (str): 模板图片的完整路径。
    - threshold (float): 匹配的置信度阈值 (0.0 到 1.0)。

    返回:
    - tuple: 如果找到，返回 (x, y, w, h, confidence)，其中 (x,y) 是左上角坐标，
             (w,h) 是模板的宽高，confidence 是匹配度。
    - None: 如果未找到或发生错误。
    """
    if not os.path.exists(template_image_path):
        print(f"错误：模板图片未找到: {template_image_path}")
        return None

    try:
        # 将屏幕截图数据转换为OpenCV图像对象 (如果它还不是的话)
        # 假设 screen_image_data 已经是 BGR numpy array
        screen_gray = cv2.cvtColor(screen_image_data, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(template_image_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"错误：无法读取模板图片: {template_image_path}")
            return None

        template_h, template_w = template.shape[:2]

        # 执行模板匹配
        # TM_CCOEFF_NORMED 方法效果较好，结果范围 [0, 1]，1表示完美匹配
        result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)

        # 获取最佳匹配的位置和相似度
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            # max_loc 是匹配到的模板左上角在屏幕截图中的坐标
            match_x, match_y = max_loc
            print(f"模板 '{os.path.basename(template_image_path)}' 找到，位置: ({match_x}, {match_y}), 置信度: {max_val:.4f}")
            return (match_x, match_y, template_w, template_h, max_val)
        else:
            # print(f"模板 '{os.path.basename(template_image_path)}' 未达到阈值 {threshold} (最高匹配度: {max_val:.4f})")
            return None

    except Exception as e:
        print(f"模板匹配过程中发生错误: {e}")
        return None