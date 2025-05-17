# 文件名: ocr_utils.py
# 位置: ring_quest_helper/core/ocr_utils.py

import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter # 确保导入这些
import cv2
import numpy as np
import traceback # 确保导入 traceback

# 可选的Pytesseract路径配置 (如果需要)
# try:
#     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# except Exception as e_path:
#     print(f"配置Pytesseract路径时出错 (可忽略，如果Tesseract已在系统PATH中): {e_path}")
#     pass

def ocr_image_region(pil_image, lang='chi_sim', psm=6, scale_factor=3, preprocess=True, assets_base_path="assets", loop_num=0, image_suffix=""):
    """
    对给定的Pillow Image对象进行OCR识别，可选择进行预处理。

    :param pil_image: PIL Image 对象。
    :param lang: OCR识别使用的语言。
    :param psm: Tesseract的页面分割模式。
    :param scale_factor: 图像放大倍数。
    :param preprocess: 是否进行预处理 (放大, 灰度, 二值化)。
    :param assets_base_path: 保存调试图片的根路径。
    :param loop_num: 当前循环次数，用于调试图片命名。
    :param image_suffix: 调试图片的文件名后缀，用于区分不同阶段的OCR。
    :return: 识别出的字符串。
    """
    try:
        if not isinstance(pil_image, Image.Image):
            print("OCR错误: 输入的不是有效的Pillow Image对象。")
            if isinstance(pil_image, str) and os.path.exists(pil_image):
                try:
                    pil_image = Image.open(pil_image)
                except Exception as e_open:
                    print(f"OCR错误：尝试打开路径为图像时失败: {e_open}")
                    return "OCR_ERROR_INVALID_IMAGE_INPUT"
            else:
                return "OCR_ERROR_INVALID_IMAGE_INPUT"

        image_to_process = pil_image
        base_filename = f"loop{loop_num}{'_' + image_suffix if image_suffix else ''}"

        if preprocess:
            # 0. (可选) 保存原始传入的PIL Image用于对比
            # try:
            #     debug_ocr_dir = os.path.join(assets_base_path, "ocr_debug")
            #     if not os.path.exists(debug_ocr_dir): os.makedirs(debug_ocr_dir, exist_ok=True)
            #     pil_image.save(os.path.join(debug_ocr_dir, f"{base_filename}_0_input_pil.png"))
            # except Exception as e_save_orig: print(f"DEBUG: 保存原始OCR输入图时出错: {e_save_orig}")

            # 1. 放大图像
            if scale_factor > 1:
                width, height = image_to_process.size
                if width == 0 or height == 0: # 避免对空图像进行resize
                    print("OCR警告: 输入图像尺寸为0，跳过放大。")
                else:
                    try:
                        image_to_process = image_to_process.resize(
                            (width * scale_factor, height * scale_factor),
                            Image.LANCZOS
                        )
                        # print(f"DEBUG (OCR Preprocess): 图像已放大到 {image_to_process.size}")
                    except Exception as e_resize:
                        print(f"DEBUG (OCR Preprocess): 图像放大失败: {e_resize}")

            # 2. 转换为OpenCV格式进行更高级处理
            cv_image_rgb = np.array(image_to_process)
            if cv_image_rgb.size == 0: # 再次检查，以防image_to_process是空图像
                print("OCR错误: 转换为OpenCV格式前的图像为空。")
                return "OCR_ERROR_EMPTY_IMAGE_FOR_CV"
            cv_image_bgr = cv2.cvtColor(cv_image_rgb, cv2.COLOR_RGB2BGR)

            # 3. 转换为灰度图
            gray_image = cv2.cvtColor(cv_image_bgr, cv2.COLOR_BGR2GRAY)
            # print("DEBUG (OCR Preprocess): 图像已转换为灰度图。")

            # 4. 二值化 (Otsu's Binarization)
            # 根据文字是深色还是浅色选择 THRESH_BINARY 或 THRESH_BINARY_INV
            # 如果文字是黄色，背景可能比它暗（在灰度图上文字可能更亮）
            # 假设黄色文字在灰度图上比深色背景更亮，我们希望文字变黑，背景变白给Tesseract
            # 或者文字变白，背景变黑。Tesseract通常对黑字白底或白字黑底都还行。
            # THRESH_BINARY: >thresh = maxval, else 0
            # THRESH_BINARY_INV: >thresh = 0, else maxval
            # 我们先假设文字比周围暗（例如任务追踪区的透明背景透出较亮游戏画面，而文字本身是黄色）
            # 或者文字是黄色，在灰度上是亮色，那么用 THRESH_BINARY_INV 可以让文字变白，其他变黑
            _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            # 如果上面效果不好，可以尝试不反转：
            # _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            # print("DEBUG (OCR Preprocess): 图像已二值化。")

            final_image_for_ocr_pil = Image.fromarray(binary_image)

            # --- (可选) 保存预处理各阶段图像用于调试 ---
            try:
                debug_ocr_dir = os.path.join(assets_base_path, "ocr_debug")
                if not os.path.exists(debug_ocr_dir): os.makedirs(debug_ocr_dir, exist_ok=True)

                if image_to_process.mode != pil_image.mode or image_to_process.size != pil_image.size : # 如果放大了
                    image_to_process.save(os.path.join(debug_ocr_dir, f"{base_filename}_1_scaled.png"))
                Image.fromarray(gray_image).save(os.path.join(debug_ocr_dir, f"{base_filename}_2_gray.png"))
                final_image_for_ocr_pil.save(os.path.join(debug_ocr_dir, f"{base_filename}_3_binary.png"))
                # print(f"DEBUG (OCR Preprocess): 已保存OCR各阶段调试图像到 '{debug_ocr_dir}'")
            except Exception as e_save:
                print(f"DEBUG: 保存OCR调试图像时出错: {e_save}")
            # ---
        else:
            final_image_for_ocr_pil = image_to_process

        custom_config = f'--oem 3 --psm {psm}'
        text = pytesseract.image_to_string(final_image_for_ocr_pil, lang=lang, config=custom_config)
        return text.strip()

    except pytesseract.TesseractNotFoundError:
        print("OCR错误: Tesseract OCR 未安装或未在系统PATH中找到。")
        return "OCR_ERROR_TESSERACT_NOT_FOUND"
    except pytesseract.TesseractError as e:
        print(f"OCR错误 (Tesseract): {e}")
        return "OCR_ERROR_TESSERACT_LANG_MISSING_OR_ERROR"
    except FileNotFoundError as e_file:
        img_path_str = pil_image if isinstance(pil_image, str) else "Pillow对象(路径未知)"
        print(f"OCR错误：找不到图像文件 '{img_path_str}'. 错误: {e_file}")
        return "OCR_ERROR_FILE_NOT_FOUND"
    except Exception as e:
        print(f"OCR过程中发生未预料的错误: {e}")
        traceback.print_exc()
        return "OCR_ERROR_UNEXPECTED"

if __name__ == '__main__':
    print("测试 ocr_utils.py...")
    # 需要一个实际的图片路径进行测试
    # test_image_path = "path_to_your_test_image_with_chinese_text.png"
    # if os.path.exists(test_image_path):
    #     text_result = ocr_image_region(Image.open(test_image_path), lang='chi_sim', psm=6, preprocess=True)
    #     print(f"OCR 测试结果: '{text_result}'")
    # else:
    #     print(f"OCR 测试图片 {test_image_path} 不存在。")
    print("ocr_utils.py 模块可被导入。请通过 main.py 进行实际测试。")