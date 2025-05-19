from paddleocr import PaddleOCR
import cv2
import matplotlib.pyplot as plt
import time

# 配置 PaddleOCR（使用 GPU 版本）
ocr = PaddleOCR(
    use_gpu=True,                 # 启用 GPU
    lang="ch",                    # 设置语言为中文
)

def recognize_text(image_path):
    """识别图片中的文字"""
    # 读取图片
    img = cv2.imread(image_path)
    if img is None:
        print(f"无法读取图片: {image_path}")
        return

    # 执行 OCR
    start_time = time.time()
    result = ocr.ocr(image_path, cls=True)
    end_time = time.time()

    print(f"识别耗时: {end_time - start_time:.2f}秒")

    # 解析结果
    texts = []
    for line in result:
        for box_info in line:
            bbox, text_info = box_info
            text, confidence = text_info
            texts.append(text)
            print(f"文本: {text}, 置信度: {confidence:.2f}")

    # 可视化结果（可选）
    visualize_ocr_result(img, result)

    return texts

def visualize_ocr_result(img, result):
    """可视化 OCR 结果"""
    # 复制原图
    img_show = img.copy()

    # 在原图上绘制检测框和识别文本
    for line in result:
        for box_info in line:
            bbox, text_info = box_info
            text, _ = text_info

            # 绘制检测框
            points = [(int(bbox[i][0]), int(bbox[i][1])) for i in range(4)]
            for i in range(4):
                cv2.line(img_show, points[i], points[(i+1)%4], (0, 255, 0), 2)

            # 添加识别文本
            cv2.putText(img_show, text, (int(bbox[0][0]), int(bbox[0][1])-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # 显示结果
    plt.figure(figsize=(10, 8))
    plt.imshow(cv2.cvtColor(img_show, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    plt.show()

if __name__ == "__main__":
    # 替换为你的图片路径
    image_path = "renshen.png"

    # 检查 GPU 是否可用
    if paddle.is_compiled_with_cuda():
        print("使用 GPU 运行")
    else:
        print("警告：未检测到 GPU 支持，将使用 CPU 运行（速度较慢）")

    # 执行 OCR
    texts = recognize_text(image_path)