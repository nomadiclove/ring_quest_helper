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


def find_contours_by_color(image_data_bgr, lower_bound_bgr, upper_bound_bgr, min_contour_area=10):
    """
    在给定的BGR图像数据中，根据颜色范围查找轮廓。

    参数:
    - image_data_bgr (numpy.ndarray): BGR格式的图像数据。
    - lower_bound_bgr (tuple): BGR颜色范围的下界 (B, G, R)。
    - upper_bound_bgr (tuple): BGR颜色范围的上界 (B, G, R)。
    - min_contour_area (int): 轮廓的最小面积，用于过滤小噪点。

    返回:
    - list: 包含所有符合条件轮廓的边界框列表 [(x, y, w, h), ...]。
            坐标是相对于输入的 image_data_bgr 的。
    """
    if image_data_bgr is None:
        print("错误 (find_contours_by_color): 输入图像数据为空。")
        return []

    try:
        # 1. 颜色过滤，创建掩码 (mask)
        mask = cv2.inRange(image_data_bgr, np.array(lower_bound_bgr), np.array(upper_bound_bgr))

        # (可选) 保存掩码图像以供调试
        cv2.imwrite("debug_color_mask.png", mask)
        print("颜色过滤掩码已保存为 debug_color_mask.png")

        # (可选) 对掩码进行形态学操作，以消除噪点或连接断裂的区域
        # kernel = np.ones((3,3), np.uint8)
        # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1) # 开运算去噪
        # mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1) # 闭运算连接区域

        # 2. 查找轮廓
        # cv2.RETR_EXTERNAL 只检测最外层的轮廓
        # cv2.CHAIN_APPROX_SIMPLE 压缩水平、垂直和对角线段，只留下它们的端点
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bounding_boxes = []
        if contours:
            for contour in contours:
                # 计算轮廓的面积
                area = cv2.contourArea(contour)
                if area >= min_contour_area:
                    # 获取轮廓的边界框 (x, y, width, height)
                    x, y, w, h = cv2.boundingRect(contour)
                    bounding_boxes.append((x, y, w, h))
                    # print(f"找到颜色区域: x={x}, y={y}, w={w}, h={h}, area={area}") # 调试用

        # (可选) 根据位置或大小对 bounding_boxes 进行排序或进一步过滤
        # 例如，按从左到右，从上到下排序
        if bounding_boxes:
            bounding_boxes.sort(key=lambda bbox: (bbox[1], bbox[0])) # 按 y 再按 x 排序

        return bounding_boxes

    except Exception as e:
        print(f"颜色轮廓查找过程中发生错误: {e}")
        return []


if __name__ == '__main__':
    # ... (已有的 find_template 测试代码保持不变) ...
    print("\n测试 image_utils.py - find_contours_by_color")

    # 你需要一张包含特定颜色区域的测试图片，例如 'debug_task_description_roi.png'
    # 并定义好颜色范围
    test_color_image_path = "debug_task_description_roi.png" # 假设这张图已生成在core目录的上一级
    # 或者直接用你项目根目录下的 debug_task_description_roi.png
    base_dir_for_color_test = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 项目根目录
    test_color_image_path_root = os.path.join(base_dir_for_color_test, "debug_task_description_roi.png")


    if os.path.exists(test_color_image_path_root):
        img_color_test_bgr = cv2.imread(test_color_image_path_root)
        if img_color_test_bgr is not None:
            # 假设我们要查找绿色，使用配置文件中的示例值 (你需要确保这些值适合你的图片)
            # BGR format: (Blue, Green, Red)
            # 对于你截图中的绿色 "贾 有钱"，可能需要调整这些值
            # 例如，绿色可能 G > 150, B < 100, R < 100
            # 先用配置文件中的值测试
            cfg_green_lower = (0, 100, 0)  # 从你的 settings.ini 截图看是 (0, 200, 0)
            cfg_green_upper = (100, 255, 100) # 从你的 settings.ini 截图看是 (50, 255, 50)

            # 使用你 settings.ini 中的精确值
            # NpcNameGreenLowerBound = 0, 200, 0
            # NpcNameGreenUpperBound = 50, 255, 50
            actual_green_lower = (0, 200, 0)
            actual_green_upper = (50, 255, 50)


            print(f"使用绿色范围: Lower={actual_green_lower}, Upper={actual_green_upper}")
            green_blobs = find_contours_by_color(img_color_test_bgr, actual_green_lower, actual_green_upper, min_contour_area=5) # min_area可以调整

            if green_blobs:
                print(f"在 '{os.path.basename(test_color_image_path_root)}' 中找到 {len(green_blobs)} 个绿色区域块:")
                # 创建一个副本用于绘制
                img_to_draw_on = img_color_test_bgr.copy()
                for i, (x, y, w, h) in enumerate(green_blobs):
                    print(f"  块 {i+1}: x={x}, y={y}, w={w}, h={h}")
                    cv2.rectangle(img_to_draw_on, (x, y), (x + w, y + h), (0, 0, 255), 1) # 红色框标记

                # 保存带有标记的图片
                cv2.imwrite("debug_found_green_blobs.png", img_to_draw_on)
                print("带有标记的绿色区域块图片已保存为 debug_found_green_blobs.png (在项目根目录)")
            else:
                print(f"在 '{os.path.basename(test_color_image_path_root)}' 中未能找到符合条件的绿色区域。请检查颜色范围或图片内容。")
        else:
            print(f"无法加载颜色测试图片: {test_color_image_path_root}")
    else:
        print(f"请确保 '{test_color_image_path_root}' 存在以进行颜色查找测试。")
        print("(通常由 main.py 在成功切割任务描述ROI后生成)")