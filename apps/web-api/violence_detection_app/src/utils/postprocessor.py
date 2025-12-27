import cv2
import numpy as np

DEFAULT_BOX_COLOR = (0, 0, 255)  #red
TEXT_COLOR = (255, 255, 255) #white
FONT = cv2.FONT_HERSHEY_SIMPLEX

def draw_boxes_on_frame(frame, result, class_names=None, conf_threshold=0.25, line_thickness=2):
    
    img = frame.copy()
    # If there are no boxes, just return frame
    if result is None or not hasattr(result, "boxes") or len(result.boxes) == 0:
        return img

    # get boxes, confidences and class ids
    try:
        xyxy = result.boxes.xyxy.cpu().numpy()         # shape (N,4)
        confs = result.boxes.conf.cpu().numpy()        # shape (N,)
        cls_ids = result.boxes.cls.cpu().numpy().astype(int)  # shape (N,)
    except Exception:
        # fallback if attributes missing
        return img

    h, w = img.shape[:2]
    for (box, conf, cls_id) in zip(xyxy, confs, cls_ids):
        if conf < conf_threshold:
            continue
        x1, y1, x2, y2 = map(int, box)
        color = DEFAULT_BOX_COLOR
        # Draw rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness=line_thickness)

        # Create label
        cls_name = class_names[cls_id] if (class_names and cls_id < len(class_names)) else str(cls_id)
        label = f"{cls_name} {conf:.2f}"

        # text size
        (tw, th), _ = cv2.getTextSize(label, FONT, fontScale=0.5, thickness=1)
        # draw filled rectangle for label background
        cv2.rectangle(img, (x1, y1 - th - 6), (x1 + tw + 6, y1), color, -1)
        # put text (in white)
        cv2.putText(img, label, (x1 + 3, y1 - 4), FONT, 0.5, TEXT_COLOR, thickness=1, lineType=cv2.LINE_AA)

    return img
