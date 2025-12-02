import cv2
import numpy as np
from ultralytics import YOLOWorld

VOCABULARY = [
    "cup", "kettle", "scissors", "fork", "book", "bottle", "bowl", "plate",
    "spoon", "knife", "remote", "cell phone", "laptop", 'lemon', 'orange',
    'apple', 'banana', 'carrot', 'cucumber', 'eggplant', 'tomato',
]

# Load YOLOv8 model
model = YOLOWorld("yolov8l-worldv2.pt")
model.set_classes(VOCABULARY)  # Set the classes to the custom vocabulary

# Read original image
image_path = 'input.jpg'
original_image = cv2.imread(image_path)
orig_h, orig_w = original_image.shape[:2]

# Resize to 640x640 for YOLO
resized_image = cv2.resize(original_image, (640, 640))

# Run inference
results = model.predict(resized_image, imgsz=640, verbose=False)

# Draw detections on original image
for box in results[0].boxes:
    cls = int(box.cls[0].item())      # Class ID
    conf = float(box.conf[0].item())  # Confidence
    xyxy = box.xyxy[0].cpu().numpy()  # Bounding box in resized image

    # Scale bbox back to original image size
    scale_x = orig_w / 640.0
    scale_y = orig_h / 640.0
    x1, y1, x2, y2 = xyxy
    x1 = int(x1 * scale_x)
    y1 = int(y1 * scale_y)
    x2 = int(x2 * scale_x)
    y2 = int(y2 * scale_y)

    # Draw bounding box and label
    cv2.rectangle(original_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    label = f"{model.names[cls]} {conf:.2f}"
    cv2.putText(original_image, label, (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# Show result
cv2.imshow('YOLOv8 world Inference', original_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

    