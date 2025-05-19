# core/text_recognizer.py
from PIL import Image
import numpy as np
import cv2 # 仍然保留，以防未来需要非常基础的图像操作或格式转换
import os
# pytesseract 相关可以完全移除了，如果我们完全转向PaddleOCR

_paddle_ocr_instance = None 

def initialize_paddle_ocr(lang='ch', use_gpu_flag=True, use_angle_cls=True):
    global _paddle_ocr_instance
    if _paddle_ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            print(f"DEBUG (recognizer): Initializing PaddleOCR with use_gpu={use_gpu_flag}, lang='{lang}'...")
            # show_log=True 可以看到PaddleOCR更详细的内部日志，调试时有用
            _paddle_ocr_instance = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang, use_gpu=use_gpu_flag, show_log=False)
            print("DEBUG (recognizer): PaddleOCR instance initialized successfully.")
        except ImportError:
            print("ERROR (recognizer): paddleocr library not found. Please run 'pip install paddleocr'")
            _paddle_ocr_instance = "error" 
        except Exception as e:
            print(f"ERROR (recognizer): Failed to initialize PaddleOCR - {e}")
            _paddle_ocr_instance = "error"
    return _paddle_ocr_instance is not None and _paddle_ocr_instance != "error"

def recognize_text_with_paddle(image_bgr, lang='ch', detail=0, use_gpu_flag=True):
    """
    Recognizes text from BGR NumPy array using PaddleOCR with its default capabilities.
    """
    if not initialize_paddle_ocr(lang=lang, use_gpu_flag=use_gpu_flag):
        # print("ERROR (recognizer): PaddleOCR not initialized or init failed during recognize call.")
        return ""  # 返回空字符串表示识别失败或引擎问题

    if _paddle_ocr_instance == "error" or image_bgr is None or image_bgr.size == 0:
        # print("ERROR (recognizer): Invalid image data or PaddleOCR engine error for paddle.")
        return "" 

    # 直接将原始BGR图像块传递给PaddleOCR
    # cv2.imwrite("debug_paddle_direct_input_to_ocr.png", image_bgr) # DEBUG: 保存实际送入OCR的图像

    result = _paddle_ocr_instance.ocr(image_bgr, cls=True) # cls=True is generally recommended

    if not result or not result[0]: # result might be [None] or [[]] if nothing found
        return "" 

    if detail == 1: # 如果调用者需要详细结果（包括坐标和置信度）
        return result[0] 
    else:
        # 提取所有识别到的文本并用空格拼接
        texts = [line[1][0] for line in result[0] if line and len(line) >= 2 and isinstance(line[1], (tuple, list)) and len(line[1]) >= 1]
        return " ".join(texts).strip()