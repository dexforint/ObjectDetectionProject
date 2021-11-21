let uploadButtonWrapper = document.getElementById('upload-button-wrapper');
let uploadButton = document.getElementById('upload-button');
let closeButton = document.getElementById('close-button');
let imageWrapper = document.getElementById('image-wrapper');
let img = document.getElementById('image');
// let canvasWrapper = document.getElementById('canvas-wrapper');
let canvas = document.getElementById('canvas');
let ctx;
if (canvas) ctx = canvas.getContext("2d");

function obj2data(obj) {
    let fd = new FormData();
    obj = JSON.stringify(obj);
    fd.append('json', obj);
    return fd;
}

let cls2color = {
    'cat': 'gray',
    'dog': 'yellow',
    'person': 'orange',
    'car': 'blue'
}

function drawRectangle(ctx, bbox, image_size) {
    // creating a square
    let cls = bbox['cls'];
    let box = bbox['box'];
    console.log(bbox);
    console.log(box);
    let [startX, startY, endX, endY] = box;
    var width = Math.abs(startX - endX);
    var height = Math.abs(startY - endY);
    let color = 'red';
    if (cls in cls2color) color = cls2color[cls];
    let lineWidth = Math.round(Math.max(image_size[0], image_size[1]) / 150);


    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth; //px
    ctx.strokeRect(startX, startY, width, height);
    
    // let lineHeight = Math.round(Math.max(image_size[0], image_size[1]) / 20);
    // console.log(lineWidth, lineHeight);
    // let x = startX;
    // let y = startY;
    // ctx.fillStyle = color;
    // ctx.fillRect(x, y, 100, lineHeight);

    // ctx.textAlign = 'center';
    // ctx.font = lineHeight + 'px Roboto';
    // ctx.fillStyle = 'black';
    // ctx.fillText(cls, x + 50, y + lineHeight / 2 + 2);
}

function serialize(form) {
    let fd = new FormData();
    for (let el of form.querySelectorAll('[name]')) {
        let name = el.getAttribute('name');
        let value;
        if (el.type == 'file') {
            value = el.files[0];
        } else if (el.value !== undefined) value = el.value;
        else value = el.innerHTML;
        fd.append(name, value);
    }
    return fd;
}

async function ajax(url, data, response_handler = null) {
    if (data.__proto__ == ({}).__proto__) data = obj2data(data);
    let response = await fetch(url, {
        method: 'POST',
        // headers: {
        //     'Content-Type': 'application/json;charset=utf-8'
        // },
        body: data
    });
    if (response.ok) {
        let response_json = await response.json();
        console.log(response_json);
        if (response_handler) response_handler(response_json);
    } else console.log("Ошибка HTTP: " + response.status);

}

function clearInputFile(f) {
    if (f.value) {
        try {
            f.value = ''; //for IE11, latest Chrome/Firefox/Opera...
        } catch (err) {}
        if (f.value) { //for IE5 ~ IE10
            var form = document.createElement('form'),
                parentNode = f.parentNode,
                ref = f.nextSibling;
            form.appendChild(f);
            form.reset();
            parentNode.insertBefore(f, ref);
        }
    }
}

function displayImage(file){
    
    img.onload = () => {
        URL.revokeObjectURL(img.src);
        imageWrapper.style.maxWidth = (document.body.clientWidth - 50) + "px";
        imageWrapper.style.maxHeight = (document.body.clientHeight - 2 * document.querySelector('.head').offsetHeight - 50) + "px";
        imageWrapper.style.display = 'block';
        uploadButtonWrapper.style.display = 'none';

        canvas.width = img.width;
        canvas.height = img.height;
    }

    img.src = URL.createObjectURL(file);
}
if (uploadButton){
    uploadButton.addEventListener('change', (event) => {
        if (!uploadButton.files || !uploadButton.files[0]) return;

        let file = uploadButton.files[0];

        displayImage(file);

        let fd = new FormData();
        fd.append('image', file);

        ajax('/detect-objects', fd, (response) => {
            if (response['ok']) {
                let bboxes = response['boxes'];
                let img_width = img.width;
                let img_height = img.height;
                console.log(bboxes);
                for (index = 0; index < bboxes.length; ++index) {
                    let bbox = bboxes[index];
                    let box = bbox['box'];
                    box[0] = Math.round(box[0] * img_width);
                    box[1] = Math.round(box[1] * img_height);
                    box[2] = Math.round(box[2] * img_width);
                    box[3] = Math.round(box[3] * img_height);
                    drawRectangle(ctx, bbox, [img_height, img_width]);
                }


                // let path = response['path'];
                // image.src = path;
            }
        });
    });
}



if (closeButton) closeButton.addEventListener('click', (event) => {
        imageWrapper.style.display = 'none';
        uploadButtonWrapper.style.display = 'block';
        clearInputFile(uploadButton);
});

window.onload = function () {
    document.querySelectorAll('.canvas:not(#canvas)').forEach((canvas) => {
        let img = canvas.parentElement.querySelector('img');

        let img_width = img.offsetWidth;
        let img_height = img.offsetHeight;
        console.log(img_width, img_height);
        canvas.width = img_width;
        canvas.height = img_height;
        let json = canvas.dataset.json;
        json = json.replaceAll("'", '"');
        let bboxes = JSON.parse(json);
        let ctx = canvas.getContext("2d");
        for (index = 0; index < bboxes.length; ++index) {
            let bbox = bboxes[index];
            let box = bbox['box'];
            box[0] = Math.round(box[0] * img_width);
            box[1] = Math.round(box[1] * img_height);
            box[2] = Math.round(box[2] * img_width);
            box[3] = Math.round(box[3] * img_height);
            drawRectangle(ctx, bbox, [img_width, img_height]);
        }
    });
};