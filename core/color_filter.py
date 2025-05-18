import cv2
import numpy as np
import os # 只是为了在可能的调试中保存图片时使用

def find_contours_by_bgr_range(image_bgr, lower_bgr, upper_bgr, min_contour_area=10):
    """
    在给定的BGR图像数据中，根据BGR颜色范围查找轮廓。

    参数:
    - image_bgr (numpy.ndarray): BGR格式的图像数据。
    - lower_bgr (tuple or list): BGR颜色范围的下界 (B, G, R)。
    - upper_bgr (tuple or list): BGR颜色范围的上界 (B, G, R)。
    - min_contour_area (int): 轮廓的最小面积，用于过滤小噪点。

    返回:
    - list: 包含所有符合条件轮廓的边界框列表 [(x, y, w, h), ...]。
            坐标是相对于输入的 image_bgr 的。
            如果未找到轮廓或发生错误，返回空列表。
    """
    if image_bgr is None:
        return []

    if not (isinstance(lower_bgr, (list, tuple)) and len(lower_bgr) == 3 and
            isinstance(upper_bgr, (list, tuple)) and len(upper_bgr) == 3):
        # print("错误 (find_contours_by_bgr_range): 颜色范围参数格式不正确。") # 暂时不打印
        return []

    try:
        # 1. 颜色过滤，创建掩码 (mask)
        # 将列表/元组转换为NumPy数组，这是cv2.inRange所期望的
        lower_bound = np.array(lower_bgr, dtype="uint8")
        upper_bound = np.array(upper_bgr, dtype="uint8")

        mask = cv2.inRange(image_bgr, lower_bound, upper_bound)

        # (可选调试) 保存掩码图像
        # project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # cv2.imwrite(os.path.join(project_root, "debug_color_filter_mask.png"), mask)
        # print("颜色过滤掩码 (color_filter.py) 已保存。")


        # (可选) 形态学操作来优化掩码
        # kernel_size = (3, 3) 
        # kernel = np.ones(kernel_size, np.uint8)
        # dilated_mask = cv2.dilate(mask, kernel, iterations=1)
        # contours_image_source = dilated_mask # 如果使用膨胀
        contours_image_source = mask # 如果不使用膨胀，直接用原始mask

        # 2. 查找轮廓
        contours, _ = cv2.findContours(contours_image_source, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bounding_boxes = []
        if contours:
            # print(f"原始找到的轮廓数量 (color_filter.py): {len(contours)}") # 暂时不打印
            for contour in contours:
                area = cv2.contourArea(contour)
                # print(f"  - 原始轮廓面积: {area:.2f}") # 暂时不打印
                if area >= min_contour_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    bounding_boxes.append((x, y, w, h))

        # 按从上到下，从左到右的顺序排序找到的边界框
        if bounding_boxes:
            bounding_boxes.sort(key=lambda bbox: (bbox[1], bbox[0]))

        return bounding_boxes

    except Exception: # 捕获所有可能的OpenCV或其他异常
        # print(f"错误 (find_contours_by_bgr_range): 颜色轮廓查找过程中发生错误 - {e}") # 暂时不打印
        # import traceback
        # traceback.print_exc() # 调试时可以打开
        return []