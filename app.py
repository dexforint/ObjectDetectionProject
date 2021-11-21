import os
from werkzeug.serving import run_simple
from api import API
import mimetypes
import json
# from PIL import Image
# from io import BytesIO

import sys
from time import time
from pathlib import Path
from db import History
from get_boxes import get_boxes
import cv2
import numpy as np

FILE = Path(__file__).absolute()
sys.path.append(FILE.parents[0].as_posix())  # add yolov5/ to path


SITE_PATH = os.getcwd()

# Directories
save_dir = "./images/processed"  # increment run


app = API()


def custom_exception_handler(request, response, exception_cls):
    response.text = "Oops! Something went wrong. Please, contact our customer support at +1-202-555-0127."


app.add_exception_handler(custom_exception_handler)


@app.route(r".+\.(css|js|jpg|png|jpeg|svg|eot|ttf|woff|woff2|ico)$")
def static_handler(request, response):
    path = SITE_PATH + request.path
    if os.path.exists(path) and not os.path.isdir(path):

        # if request.if_none_match.__str__()[1:-1] == caching[request.path]:
        #     response.status = 304
        # else:
        response.status = 200
        # response.etag = caching[request.path]
        content_type = mimetypes.guess_type(path)[0]

        response.content_type = content_type

        response.cache_control = "max-age=86400; public"

        with open(path, 'rb') as f:
            response.body = f.read()
    else:
        response.status = 404

def add_to_db(image_name, boxes):
    History.create(image_name=image_name, boxes=boxes)


def detector(image_data):
    print("Detector")
    # img = Image.open(BytesIO(image_data))

    img = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_height, img_width, _ = img.shape

    n = len(os.listdir("./images")) + 1
    n = str(n)
    n = "0" * (3 - len(n)) + n
    image_name = f"{n}.jpg"
    cv2.imwrite(f"./images/{image_name}", img)

    t1 = time()
    boxes = get_boxes([img])[0]
    for bbox in boxes:
        box = bbox['box']
        box[0] /= img_width
        box[1] /= img_height
        box[2] /= img_width
        box[3] /= img_height
        
    t2 = time()
    diff = round(t2 - t1, 1)
    print(f"Detection time:{diff}s")
    add_to_db(image_name, boxes)
    print(boxes)
    return boxes


@app.route("/detect-objects")
def detect_object(request, response):
    POST = request.POST
    image_data = POST['image']

    boxes = detector(image_data.value)

    resp_obj = {
        'ok': True,
        'boxes': boxes
    }

    response.text = json.dumps(resp_obj)


@app.route("/")
def main(request, response):
    response.status_code = 200
    with open("./index.html", 'rb') as f:
        response.body = f.read()

def get_images_html():
    string = ""
    query = History.select().order_by(History.datetime.desc())
    for row in query:
        json_string = str(row.boxes)
        print(json_string)
        string += f"<div class='image-wrap'><canvas class='canvas' data-json=\"{json_string}\"></canvas>><img class='image' src='/images/{row.image_name}'></div>"

    return string

@app.route("/history")
def main(request, response):
    response.status_code = 200
    with open("./history.html", 'rb') as f:
        html_code = f.read().decode("utf-8")

    images_html = get_images_html()

    html_code = html_code.replace("STRING_FOR_REPLACE", images_html)

    html_code = bytes(html_code, 'UTF-8')
    response.body = html_code

@app.route(r".+")
def page404(request, response):
    response.status = 404


if "PORT" in os.environ:
    port = int(os.environ.get("PORT", 6666))
    hostname = '0.0.0.0'
else:
    port = 6666
    hostname = '0.0.0.0'
print(hostname, port)
run_simple(hostname, port, app, use_reloader=False)
