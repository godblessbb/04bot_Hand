import openai
from PIL import Image, ImageDraw
from io import BytesIO
import base64
import json

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

# Load your API key
openai.api_key = "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"

# Load image
image_path = "/home/hoang-dung/Downloads/test.jpg"
image = Image.open(image_path)

# Convert to binary for upload
with open(image_path, "rb") as img_file:
    image_bytes = img_file.read()

# Encode image to base64
base64_image = base64.b64encode(image_bytes).decode("utf-8")
image_data_url = f"data:image/jpeg;base64,{base64_image}"

# Call the GPT-4o Vision model using the new SDK format
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": SYSTEM_PROMT,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Give me some fruits"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url
                    }
                }
            ]
        }
    ],
    temperature=0
)

# Extract JSON from assistant's reply
reply = response.choices[0].message.content
print("Raw response:", reply)

# Parse JSON from string
try:
    actions = json.loads(reply)
except json.JSONDecodeError:
    actions = eval(reply)  # fallback if it's a Python-like list

# Draw bounding boxes
image = Image.open(image_path)
draw = ImageDraw.Draw(image)
for act in actions:
    bbox = act["bbox"]
    label = act["target"]
    draw.rectangle(bbox, outline="red", width=3)
    draw.text((bbox[0], bbox[1] - 10), label, fill="red")

# Show result
image.show()