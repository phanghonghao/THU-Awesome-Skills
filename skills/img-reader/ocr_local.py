"""
ocr_local.py - 本地 OCR 识别图片文字（离线，无需联网）
使用 PaddleOCR PP-OCRv4
"""
import sys
import os
import json


def check_paddleocr():
    """检查 PaddleOCR 是否已安装"""
    try:
        import paddleocr
        return True
    except ImportError:
        return False


def install_paddleocr():
    """安装 PaddleOCR"""
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paddleocr", "paddlepaddle", "-q"])


def ocr_image(image_path, lang="ch"):
    """使用 PaddleOCR 识别图片中的文字

    Args:
        image_path: 图片路径
        lang: 语言, 'ch'=中英文, 'en'=英文

    Returns:
        dict: {success, text_lines: [{text, confidence, bbox}], full_text}
    """
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
    result = ocr.ocr(image_path, cls=True)

    text_lines = []
    if result and result[0]:
        for line in result[0]:
            bbox = line[0]
            text = line[1][0]
            confidence = line[1][1]
            text_lines.append({
                "text": text,
                "confidence": round(confidence, 4),
                "bbox": bbox
            })

    full_text = "\n".join([t["text"] for t in text_lines])

    return {
        "success": True,
        "text_lines": text_lines,
        "full_text": full_text,
        "line_count": len(text_lines)
    }


def ocr_table(image_path, lang="ch"):
    """使用 PP-Structure 提取图片中的表格

    Args:
        image_path: 图片路径
        lang: 语言

    Returns:
        dict: {success, tables: [html_str], text_lines}
    """
    from paddleocr import PPStructure

    table_engine = PPStructure(show_log=False, lang=lang)
    result = table_engine(image_path)

    tables = []
    texts = []
    for item in result:
        if item["type"] == "table":
            tables.append(item.get("res", {}).get("html", ""))
        elif item["type"] in ("text", "title", "figure_caption"):
            text = item.get("res", [])
            if isinstance(text, list):
                for t in text:
                    texts.append(t.get("text", ""))
            elif isinstance(text, str):
                texts.append(text)

    return {
        "success": True,
        "tables": tables,
        "table_count": len(tables),
        "text_lines": texts,
        "full_text": "\n".join(texts)
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_local.py <image_path> [--table] [--install]")
        sys.exit(1)

    image_path = sys.argv[1]
    use_table = "--table" in sys.argv

    if "--install" in sys.argv or not check_paddleocr():
        print("Installing PaddleOCR...")
        install_paddleocr()
        print("Done.")

    if use_table:
        result = ocr_table(image_path)
    else:
        result = ocr_image(image_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))
