# core/text_recognizer.py
from PIL import Image # PaddleOCR 可能内部会用到，或者返回Pillow Image
import numpy as np
import cv2 # 仍然需要用于可能的颜色空间转换或基本操作
import os
# pytesseract 可以完全移除了，如果我们确定用PaddleOCR

_paddle_ocr_instance = None 

def initialize_paddle_ocr(lang='ch', use_gpu_flag=True, use_angle_cls=True):
    global _paddle_ocr_instance
    if _paddle_ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            print(f"DEBUG (recognizer): Initializing PaddleOCR with use_gpu={use_gpu_flag}, lang='{lang}'...")
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
    Recognizes text from BGR NumPy array using PaddleOCR with minimal preprocessing.
    """
    if not initialize_paddle_ocr(lang=lang, use_gpu_flag=use_gpu_flag):
        print("ERROR (recognizer): PaddleOCR not initialized or init failed.")
        return "" 

    if _paddle_ocr_instance == "error" or image_bgr is None or image_bgr.size == 0:
        print("ERROR (recognizer): Invalid image data or PaddleOCR engine error.")
        return "" 

    # PaddleOCR的ocr方法直接接收BGR NumPy数组
    # 我们不在这里做额外的放大或复杂的预处理，直接将切割的小块喂给它
    # cv2.imwrite("debug_paddle_direct_input_blob.png", image_bgr) # DEBUG: 保存直接送入PaddleOCR的图像块

    result = _paddle_ocr_instance.ocr(image_bgr, cls=True) 

    if not result or not result[0]:
        return "" 

    if detail == 1:
        return result[0] 
    else:
        texts = [line[1][0] for line in result[0] if line and len(line) >= 2 and len(line[1]) >=1]
        return " ".join(texts).strip()