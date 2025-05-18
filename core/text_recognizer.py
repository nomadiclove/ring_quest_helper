import pytesseract
from PIL import Image
import numpy as np
import cv2
import os

# 全局配置Tesseract OCR的路径 (如果需要的话)
# 在Replit上通常不需要。在本地Windows，如果Tesseract未添加到PATH，
# 取消注释并修改为你的Tesseract安装路径下的tesseract.exe
# try:
#     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# except Exception:
#     pass # 如果设置失败，后续调用时会报错 TesseractNotFoundError

def _preprocess_for_ocr(image_bgr, upscale_factor=1.0, binarize=False, binarize_threshold=128):
    """
    对图像进行预处理以优化OCR结果。
    私有辅助函数。

    参数:
    - image_bgr (numpy.ndarray): BGR格式的图像数据。
    - upscale_factor (float): 图像放大因子，1.0表示不放大。
    - binarize (bool): 是否进行二值化处理。
    - binarize_threshold (int): 二值化时使用的阈值 (如果不是OTSU)。

    返回:
    - PIL.Image: 预处理后的Pillow Image对象 (RGB格式，Tesseract期望)。
    """
    if image_bgr is None:
        return None

    # 1. 转换为灰度图
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # 2. (可选) 放大图像
    if upscale_factor > 1.0:
        width = int(gray.shape[1] * upscale_factor)
        height = int(gray.shape[0] * upscale_factor)
        dim = (width, height)
        # 使用 INTER_CUBIC 或 INTER_LINEAR 进行放大，CUBIC通常效果更好但慢一点
        gray = cv2.resize(gray, dim, interpolation=cv2.INTER_CUBIC) 

    # 3. (可选) 二值化
    if binarize:
        # THRESH_BINARY_INV 对于深色背景浅色文字可能效果好
        # THRESH_OTSU 可以自动寻找最佳阈值
        # 你可能需要根据实际图像调整阈值和类型
        _, gray = cv2.threshold(gray, binarize_threshold, 255, cv2.THRESH_BINARY) # 或者 cv2.THRESH_OTSU
        # cv2.imwrite("debug_ocr_binarized.png", gray) # 调试用

    # 将处理后的灰度NumPy数组转换为Pillow Image对象 (Tesseract期望RGB)
    # 如果是灰度图，cvtColor到RGB会复制灰度通道到R,G,B
    pil_image = Image.fromarray(cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB))
    return pil_image


def recognize_text(image_bgr, lang='chi_sim', psm=7, 
                   upscale_factor=1.0, binarize=False, binarize_threshold=128,
                   custom_oem_config=3):
    """
    从给定的图像数据 (NumPy BGR array) 中识别文本。

    参数:
    - image_bgr (numpy.ndarray): BGR格式的图像数据。
    - lang (str): Tesseract OCR 使用的语言包 (例如 'chi_sim', 'eng')。
    - psm (int): Tesseract Page Segmentation Mode。
                 7: "Treat the image as a single text line."
                 8: "Treat the image as a single word."
                 13: "Raw line. Treat the image as a single text line, bypassing hacks."
                 6: "Assume a single uniform block of text."
                 3: "Fully automatic page segmentation, but no OSD." (默认)
    - upscale_factor (float): 预处理时图像放大因子。
    - binarize (bool): 预处理时是否进行二值化。
    - binarize_threshold (int): 二值化阈值。
    - custom_oem_config (int): Tesseract OCR Engine Mode (0-3). 3 is default.

    返回:
    - str: 识别出的文本，去除首尾空白和换行符。
    - None: 如果图像数据无效、识别失败或发生Tesseract错误。
    """
    if image_bgr is None or image_bgr.size == 0:
        return None

    try:
        pil_image_for_ocr = _preprocess_for_ocr(image_bgr, upscale_factor, binarize, binarize_threshold)
        if pil_image_for_ocr is None:
            return None

        custom_config = f'--oem {custom_oem_config} --psm {psm}'
        text = pytesseract.image_to_string(pil_image_for_ocr, lang=lang, config=custom_config)

        cleaned_text = text.strip().replace('\n', ' ').replace('\r', ' ')
        return cleaned_text
    except pytesseract.TesseractNotFoundError:
        # print("错误 (recognize_text): Tesseract OCR 未安装或未在PATH中。") # 暂时不打印
        # print("请确保已安装Tesseract并正确配置 (如果需要)。")
        return None # 或者可以考虑向上抛出此异常，让调用者处理
    except Exception: # 捕获其他可能的 pytesseract 或 PIL 错误
        # print(f"错误 (recognize_text): OCR识别过程中发生错误 - {e}") # 暂时不打印
        # import traceback
        # traceback.print_exc() # 调试时可以打开
        return None