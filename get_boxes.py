from models.experimental import attempt_load
from utils.general import non_max_suppression, scale_coords, xyxy2xywh
import cv2
import torch
import numpy as np

def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True, stride=32):
    # Resize and pad image while meeting stride-multiple constraints
    shape = im.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better val mAP)
        r = min(r, 1.0)

    # Compute padding
    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - \
        new_unpad[1]  # wh padding
    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = new_shape[1] / shape[1], new_shape[0] / \
            shape[0]  # width, height ratios

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right,
                            cv2.BORDER_CONSTANT, value=color)  # add border
    return im, ratio, (dw, dh)


weights = 'yolov5s.pt'
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
model = attempt_load(weights, map_location=device)
names = model.module.names if hasattr(
    model, 'module') else model.names 

@torch.no_grad()
def get_boxes(
        images,
        imgsz=[640, 640],
        conf_thres=0.5,
        iou_thres=0.6,
        max_det=100,
        classes=None  #[0, 14, 15, 16],
):
    global device, model
    if device.type != 'cpu':
        # run once
        model(torch.zeros(1, 3, *imgsz).to(device).type_as(next(model.parameters())))

    arr = []
    for img in images:
        orig_shape = img.shape
        img, ratio, (dw, dh) = letterbox(img)

        img = torch.from_numpy(img).to(device)
        img = img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if len(img.shape) == 3:
            img = img[None]  # expand for batch dim

        # Inference
        img = img.permute(0, 3, 1, 2)
        pred = model(img, augment=False)[0]

        # NMS
        pred = non_max_suppression(
            pred, conf_thres, iou_thres, classes, False, max_det=max_det)

        # Process predictions
        bboxes = []
        for i, det in enumerate(pred):  # per image

            # normalization gain whwh
            #gn = torch.tensor(orig_shape)[[1, 0, 1, 0]]
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(
                    img.shape[2:], det[:, :4], orig_shape).round()

                for *xyxy, conf, cls in reversed(det):
                    #xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                    cls = int(cls)
                    conf = float(conf)
                    xyxy = [int(el) for el in xyxy]
                    bboxes.append({
                        'cls': names[cls],
                        'conf': conf,
                        'box': xyxy
                    })

        arr.append(bboxes)

    return arr
