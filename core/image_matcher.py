import cv2
import numpy as np
import os

def find_template_in_image(main_image_bgr, template_image_path, threshold=0.8):
    """
    在给定的主图像 (BGR格式) 中查找模板图片。

    参数:
    - main_image_bgr (numpy.ndarray): BGR格式的主图像数据，我们将在其中搜索。
    - template_image_path (str): 模板图片的完整路径。
    - threshold (float): 匹配的置信度阈值 (0.0 到 1.0)。

    返回:
    - tuple: 如果找到，返回 (x, y, w, h, confidence)，其中 (x,y) 是模板在主图像中
             的左上角坐标，(w,h) 是模板的宽高，confidence 是匹配度。
    - None: 如果未找到、模板无法加载或发生其他错误。
    """
    if main_image_bgr is None:
        # print("错误 (find_template_in_image): 主图像数据为空。") # 遵循原则，暂时不打印
        return None

    if not os.path.exists(template_image_path):
        # print(f"错误 (find_template_in_image): 模板图片未找到: {template_image_path}") # 暂时不打印
        return None

    try:
        template_bgr = cv2.imread(template_image_path) # 读取彩色模板
        if template_bgr is None:
            # print(f"错误 (find_template_in_image): 无法读取模板图片: {template_image_path}") # 暂时不打印
            return None

        # 转换为灰度图进行匹配，通常更稳定且对颜色变化不那么敏感
        main_gray = cv2.cvtColor(main_image_bgr, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

        template_h, template_w = template_gray.shape[:2]

        # 执行模板匹配
        # TM_CCOEFF_NORMED 方法效果较好，结果范围 [-1, 1] 或 [0, 1] (取决于OpenCV版本和具体实现细节，通常是归一化的)
        # 对于灰度图，其值在匹配良好时接近1
        result = cv2.matchTemplate(main_gray, template_gray, cv2.TM_CCOEFF_NORMED)

        # 获取最佳匹配的位置和相似度
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            match_x, match_y = max_loc # 左上角坐标
            # print(f"模板 '{os.path.basename(template_image_path)}' 找到，位置: ({match_x}, {match_y}), 置信度: {max_val:.4f}") # 暂时不打印
            return (match_x, match_y, template_w, template_h, max_val)
        else:
            # print(f"模板 '{os.path.basename(template_image_path)}' 未达到阈值 {threshold} (最高匹配度: {max_val:.4f})") # 暂时不打印
            return None

    except Exception: # 捕获所有可能的OpenCV或其他异常
        # print(f"错误 (find_template_in_image): 模板匹配过程中发生错误 - {e}") # 暂时不打印
        return None