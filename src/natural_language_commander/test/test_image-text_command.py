      
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import json
import base64
from groq import Groq, BadRequestError, NotFoundError
import cv2
import numpy as np

SYSTEM_PROMT = """You are an AI robot controller. Your job is to break down natural language commands into a structured list of actions for a robotic arm.

Given an image of the robot's view and a user command, return a list of actions in JSON format. Each action must include:

- action: the robot action to perform (e.g., "pick", "place", "push", "open", "pour" etc.)

- target: a description of the object involved

- bbox: the bounding box of the object in [x1, y1, x2, y2] format (normalized or pixel-wise)

If no relevant object is found, return an empty list. Given the image size: 1080x1920

**Expected Output Format (JSON):**


json

[

{

"action": <action>,

"target": <object or human>,

"bbox": <bounding_box>

},

{

"action": <action>,

"target": <object or human>,

"bbox": <bounding_box>

}

]"""

def load_image_as_base64(path: str, max_dim=256, quality=30) -> str:
    img_cv = cv2.imread(path)
    if img_cv is None:
        raise FileNotFoundError(f"Image not found: {path}")
    h, w = img_cv.shape[:2]
    scale = max_dim / max(h, w)
    if scale < 1.0:
        img_cv = cv2.resize(img_cv, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    _, buf = cv2.imencode('.jpg', img_cv, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    img_b64 = base64.b64encode(buf).decode()
    return img_b64, img_cv

def main():
    # 1. 用户输入
    img_path = "/home/hoang-dung/Downloads/test.jpg"  # 替换为你的图片路径
    cmd = input("请输入操作指令: ").strip()

    # 2. 准备 prompt
    img_b64, img_raw = load_image_as_base64(img_path)
    system_prompt = SYSTEM_PROMT

    user_prompt = (
        f"![image](data:image/jpeg;base64,{img_b64})\n\n"
        f"请解析这条指令：{cmd}"
    )

    # 3. 初始化 Groq 客户端（直接在脚本中写入密钥）
    groq_api_key = "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"  # ← 在这里填写你从 Groq 控制台获取的实际 API Key，不要带多余空格或引号之外的字符
    client = Groq(api_key=groq_api_key)

    # 4. 使用 Groq Chat Completion 接口
    # try:
    #     resp = client.chat.completions.create(
    #         model="meta-llama/llama-4-maverick-17b-128e-instruct",
    #         messages=[
    #             {"role": "system", "content": system_prompt},
    #             {"role": "user", "content": user_prompt}
    #         ]
    #     )
    #     raw = resp.choices[0].message.content.strip()
    # except BadRequestError as e:
    #     print(f"请求错误：{e}")
    #     return
    # except NotFoundError:
    #     print("模型未找到，请确认模型名称是否正确或你的账户是否有访问权限。")
    #     return

    # 5. 解析并打印
    # try:
    #     result = json.loads(raw)
    # except json.JSONDecodeError:
    #     print(raw)
    #     return

    # print(json.dumps(result, ensure_ascii=False, indent=2))
    result = [
        {
            "action": "pick",
            "target": "orange",
            "bbox": [0.26, 0.15, 0.74, 0.40]
        },
        {
            "action": "pick",
            "target": "lemon",
            "bbox": [0.30, 0.48, 0.70, 0.68]
        }
    ]
    h, w = img_raw.shape[:2]

    for action in result:
        print(f"Action: {action['action']}, Target: {action['target']}, Bounding Box: {action['bbox']}")

        bb = action.get("bbox")
        target = action.get("target")
        if bb and len(bb) == 4:
            bb[0] *= w
            bb[1] *= h
            bb[2] *= w
            bb[3] *= h

            # Draw rectangle and label
            pt1 = (int(bb[0]), int(bb[1]))
            pt2 = (int(bb[2]), int(bb[3]))
            cv2.rectangle(img_raw, pt1, pt2, (0, 0, 255), 3)
            cv2.putText(img_raw, str(target), (pt1[0], max(pt1[1] - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow("Image", img_raw)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

    