# core/text_recognizer.py
import pytesseract # Keep for Tesseract as a fallback or alternative
from PIL import Image
import numpy as np
import cv2
import os

_paddle_ocr_instance = None 

def initialize_paddle_ocr(lang='ch', use_gpu_flag=True, use_angle_cls=True):
    global _paddle_ocr_instance
    if _paddle_ocr_instance is None: # Only initialize if not already done or errored
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
    # Return True if instance is valid, False if initialization failed
    return _paddle_ocr_instance is not None and _paddle_ocr_instance != "error"


def recognize_text_with_paddle(image_bgr, lang='ch', detail=0, use_gpu_flag=True):
    if not initialize_paddle_ocr(lang=lang, use_gpu_flag=use_gpu_flag):
        print("ERROR (recognizer): PaddleOCR not initialized or initialization failed during recognize call.")
        return "" 

    if _paddle_ocr_instance == "error" or image_bgr is None or image_bgr.size == 0:
        return "" 

    # PaddleOCR's ocr method might raise exceptions on its own
    result = _paddle_ocr_instance.ocr(image_bgr, cls=True) 

    if not result or not result[0]:
        return "" 

    if detail == 1:
        return result[0] 
    else:
        texts = [line[1][0] for line in result[0] if line and len(line) >= 2 and len(line[1]) >=1]
        return " ".join(texts).strip()

# --- Tesseract OCR (kept as an alternative, can be removed if PaddleOCR is primary) ---
def _preprocess_for_tesseract(image_bgr, upscale_factor=1.0, binarize=False, binarize_threshold=128):
    if image_bgr is None: return None
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    if upscale_factor > 1.0:
        width = int(gray.shape[1] * upscale_factor)
        height = int(gray.shape[0] * upscale_factor)
        gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC) 
    if binarize:
        _, gray = cv2.threshold(gray, binarize_threshold, 255, cv2.THRESH_BINARY)
    return Image.fromarray(cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB))

def recognize_text_with_tesseract(image_bgr, lang='chi_sim', psm=7, 
                                   upscale_factor=1.0, binarize=False, binarize_threshold=128,
                                   custom_oem_config=3):
    if image_bgr is None or image_bgr.size == 0: return ""
    # try: # Removed per principle
    pil_image_for_ocr = _preprocess_for_tesseract(image_bgr, upscale_factor, binarize, binarize_threshold)
    if pil_image_for_ocr is None: return ""
    custom_config = f'--oem {custom_oem_config} --psm {psm}'
    text = pytesseract.image_to_string(pil_image_for_ocr, lang=lang, config=custom_config)
    return text.strip().replace('\n', ' ').replace('\r', ' ')
    # except pytesseract.TesseractNotFoundError:
    #     print("ERROR (recognizer): Tesseract OCR not installed or not in PATH.")
    #     return ""
    # except Exception:
    #     return ""