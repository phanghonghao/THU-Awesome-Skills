"""
vision_api.py - 通过免费 VLM API 分析图片（零 MCP 额度）
支持: GLM-4V-Flash (免费)
"""
import base64
import sys
import os
import json


def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_glm4v(image_path, prompt="请详细描述这张图片中的所有内容，包括文字"):
    """GLM-4V-Flash (免费) - 智谱 AI"""
    from zhipuai import ZhipuAI

    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        # 尝试从 .env 文件读取
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            for line in open(env_path, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == "ZHIPU_API_KEY":
                        api_key = v.strip().strip('"').strip("'")
                        break

    if not api_key:
        return {"success": False, "error": "ZHIPU_API_KEY not set. Get free key at https://open.bigmodel.cn"}

    client = ZhipuAI(api_key=api_key)
    img_b64 = encode_image(image_path)

    resp = client.chat.completions.create(
        model="glm-4v-flash",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text", "text": prompt}
            ]
        }]
    )
    return {"success": True, "result": resp.choices[0].message.content, "provider": "glm-4v-flash"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vision_api.py <image_path> [prompt]")
        sys.exit(1)

    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "请详细描述这张图片中的所有内容，包括文字"

    result = analyze_glm4v(image_path, prompt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
