import pytesseract
from PIL import Image # pytesseract 可以直接处理 Pillow Image 对象
import numpy as np
import cv2 # 主要用于可能的图像预处理

# 尝试配置 Tesseract OCR 的路径 (如果需要的话)
# 在 Replit 上通常不需要手动配置，因为它可能已经安装在标准路径
# 如果在你的本地 Windows 环境运行，并且 Tesseract 没有添加到 PATH，你可能需要取消注释并修改下面这行：
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # 修改为你的Tesseract安装路径

def preprocess_for_ocr(image_data_bgr):
    """
    对图像进行预处理，以提高OCR识别率。
    - 转为灰度图
    - (可选) 二值化处理
    - (可选) 降噪
    参数:
    - image_data_bgr (numpy.ndarray): BGR格式的图像数据。
    返回:
    - numpy.ndarray: 预处理后的图像数据 (灰度)。
    """
    gray = cv2.cvtColor(image_data_bgr, cv2.COLOR_BGR2GRAY)

    # (可选) 应用高斯模糊降噪，对于小字体有时有帮助，有时会起反作用
    # gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # (可选) 应用阈值进行二值化，对于对比度明显的文字效果好
    # _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # return thresh

    # (可选) 放大图像，对于小字体识别有奇效
    # scale_factor = 2
    # width = int(gray.shape[1] * scale_factor)
    # height = int(gray.shape[0] * scale_factor)
    # dim = (width, height)
    # resized_gray = cv2.resize(gray, dim, interpolation=cv2.INTER_LINEAR) # 或者 INTER_CUBIC
    # return resized_gray

    return gray # 目前只做灰度转换，后续根据需要添加其他预处理

def recognize_text_from_image_data(image_data_bgr, lang='chi_sim', psm=6):
    """
    从给定的图像数据 (NumPy BGR array) 中识别文本。

    参数:
    - image_data_bgr (numpy.ndarray): BGR格式的图像数据。
    - lang (str): Tesseract OCR 使用的语言包 (例如 'chi_sim' 表示简体中文, 'eng' 表示英文)。
    - psm (int): Tesseract Page Segmentation Mode (页面分割模式)。
                 默认为 6: "Assume a single uniform block of text."
                 其他常用模式：
                 3: "Fully automatic page segmentation, but no OSD." (默认)
                 7: "Treat the image as a single text line."
                 11: "Sparse text. Find as much text as possible in no particular order."
                 13: "Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific."

    返回:
    - str: 识别出的文本，去除首尾空白。
    - None: 如果识别失败或发生错误。
    """
    try:
        # 图像预处理
        processed_image = preprocess_for_ocr(image_data_bgr)

        # 将处理后的 NumPy 数组转换为 Pillow Image 对象，因为 pytesseract 更喜欢 Pillow Image
        pil_image = Image.fromarray(cv2.cvtColor(processed_image, cv2.COLOR_GRAY2RGB)) # Tesseract期望RGB

        # 构建 Tesseract 配置字符串
        # 例如，使用 PSM 6 (假设是单行或一小块文本)
        custom_config = f'--oem 3 --psm {psm}' # OEM 3 是默认引擎

        text = pytesseract.image_to_string(pil_image, lang=lang, config=custom_config)

        # 清理识别结果，去除可能的换行符和多余空格
        cleaned_text = text.strip().replace('\n', ' ').replace('\r', ' ')
        # print(f"OCR Raw Result: '{text.strip()}', Cleaned: '{cleaned_text}'") # 调试用
        return cleaned_text
    except pytesseract.TesseractNotFoundError:
        print("错误: Tesseract OCR 未安装或未在系统PATH中找到。")
        print("请确保已安装 Tesseract OCR 并正确配置了路径 (如果需要)。")
        return None
    except Exception as e:
        print(f"OCR识别过程中发生错误: {e}")
        return None

# --- 简单测试 ---
if __name__ == '__main__':
    print("测试 ocr_utils.py - recognize_text_from_image_data")
    # 你需要一张包含中文文本的测试图片 'test_ocr_image.png' 放在脚本同级目录
    # 或者修改路径
    test_image_path = "test_ocr_image.png" 
    if os.path.exists(test_image_path):
        img_bgr = cv2.imread(test_image_path)
        if img_bgr is not None:
            # 模拟识别任务类型，通常是一小块文本
            recognized_text = recognize_text_from_image_data(img_bgr, lang='chi_sim', psm=6) 
            if recognized_text:
                print(f"测试图片 '{test_image_path}' 识别结果 (psm=6): '{recognized_text}'")
            else:
                print(f"未能从 '{test_image_path}' 识别出文本。")

            # 模拟识别多行描述，可能需要不同的psm
            # recognized_text_block = recognize_text_from_image_data(img_bgr, lang='chi_sim', psm=3)
            # if recognized_text_block:
            #     print(f"测试图片 '{test_image_path}' 识别结果 (psm=3): '{recognized_text_block}'")

        else:
            print(f"无法加载测试图片: {test_image_path}")
    else:
        print(f"请创建测试图片 '{test_image_path}' 以进行OCR基本测试。")
        print("图片中应包含一些简体中文文字。")