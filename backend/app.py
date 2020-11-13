from flask import Flask, request, jsonify, json, abort, redirect, url_for, render_template, send_file, Response
from flask_cors import CORS, cross_origin
import os
import re
import subprocess
import threading
import traceback
import base64
import requests
import json
import uuid
import re
import io
import PIL
from PIL import Image
import werkzeug
from werkzeug.routing import PathConverter
from packaging import version


app = Flask(__name__, template_folder='template')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


# whether or not merge_slashes is available and true
MERGES_SLASHES = version.parse(werkzeug.__version__) >= version.parse("1.0.0")

class EverythingConverter(PathConverter):
    regex = '.*?'

app.url_map.converters['everything'] = EverythingConverter

myapp = {}
myenvs = {
    "port": "MYGALLERY_PORT",
    "folder": "MYGALLERY_ROOT"
}
for key, envpath in myenvs.items():
    val = os.environ.get(envpath, "-")
    if val == "-":
        raise Exception(f"ENV {envpath} not set")
    myapp[key] = val
folder = myapp["folder"]
tfolder = f"{folder}/thumbs/"
mfolder = f"{folder}/main/"
metafolder = f"{folder}meta/"
for f2 in [folder, tfolder, mfolder, metafolder]:
    if not os.path.exists(f2):
        os.mkdir(f2)
datatrack = f"{folder}track.json"
if not os.path.exists(datatrack):
    vault = {"hash": {}, "rev": {}}
else:
    with open(datatrack) as f:
        vault = json.load(f)
#{"hash": {"all": "4d7a0459fb694876a8ffc68ff906fbc4", ...
# "rev": {"4d7a0459fb694876a8ffc68ff906fbc4": "all", ...

def get_serial():
    return uuid.uuid4().hex

def save_vault():
    with open(datatrack, "w") as f:
        json.dump(vault, f)

def load_json(filepath):
    with open(filepath) as f:
        data = json.load(f)
    return data

def save_json(data, filepath):
    with open(filepath, "w") as f:
        json.dump(data, f)

def validate_path(path):
    path = re.sub('/{2,}', '/', path)
    if path[0] == '/':
        path = path[1:]
    if path[-1] == '/':
        path = path[:-1]
    if not path in vault['hash']:
        serial = get_serial()
        while serial in vault['rev']:
            serial = get_serial()
        metapath = f"{metafolder}/{serial}.txt"
        with open(metapath, 'w') as f:
            f.write("")
        vault['hash'][path] = serial
        vault['rev'][serial] = path
        save_vault()
    else:
        serial = vault['hash'][path]
    return serial

def add_img(pathenc, serialimg):
    filepath = f"{metafolder}/{pathenc}.txt"
    data = open(filepath).read().split("\n")
    data = [d for d in data if d != ""]
    data.append(serialimg)
    with open(filepath, 'w') as f:
        f.write("\n".join(data))

@app.route('/search/<path>', methods=['GET'])
@cross_origin()
def r_search(path=""):
    ret = []
    if path == "":
        ret = list(vault.keys())[:10]
    else:
        path = base64.b64decode(path).decode().lower()
        lim = 10
        for k in vault.get('hash', {}):
            if path in k.lower():
                ret.append(k)
            if len(ret) == lim:
                break
    ret = {k:None for k in ret}
    return jsonify(ret)

@app.route('/thumb/<img>', methods=['GET'])
@cross_origin()
def thumb(img):
    lfolder = tfolder
    filepath = f"{lfolder}/{img}"
    if os.path.exists(filepath):
        return send_file(filepath)
    return ""

@app.route('/image/<img>', methods=['GET'])
@cross_origin()
def img(img):
    lfolder = mfolder
    filepath = f"{lfolder}/{img}"
    if os.path.exists(filepath):
        return send_file(filepath)
    return ""

@app.route('/del', methods=['GET', 'POST'])
@cross_origin()
def delname():
    req = request.json

    name = req['name']
    path = req['path']
    if path in vault['hash']:
        filepath = f"{metafolder}/{vault['hash'][path]}.json"
        files = load_json(filepath)

        files = [f for f in files if f != name]
        save_json(files, filepath)

    return "ok"

def download_image(link):
    rs = requests.get(link)
    return base64.b64encode(rs.content).decode()

#https://stackoverflow.com/questions/48229318/how-to-convert-image-pil-into-base64-without-saving/48229407
#ty @Taha Mahjoubi
def img_to_base64_str(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    buffered.seek(0)
    img_byte = buffered.getvalue()
    img_str = "data:image/png;base64," + base64.b64encode(img_byte).decode()
    return img_str

@app.route('/recv', methods=['GET', 'POST'])
@cross_origin()
def recv():
    uploaded_file = request.files.to_dict()
    if uploaded_file:
        req = request.form.to_dict()
        path = req['path']
        pathenc = validate_path(path)
        for k,image in uploaded_file.items():
            img = Image.open(image)
            save_image(pathenc, img_to_base64_str(img))
        return 'ok'

    req = request.json

    if not 'image64' in req:
        return 'nothing'

    image = req['image64']
    path = req['path']
    print(path)
    print(image[:30])
    if "http" == image[:4]:
        image = download_image(image)
    pathenc = validate_path(path)

    return save_image(pathenc, image)

def save_image(pathenc, image):
    serial = get_serial()
    while os.path.exists(f"{mfolder}/{serial}.png"):
        serial = get_serial()

    m_filepath = f"{mfolder}/{serial}.png"
    t_filepath = f"{tfolder}/{serial}.png"

    img = imgfromb64(image)
    img.save(m_filepath, 'PNG')

    size = 256, 256
    img.thumbnail(size, Image.ANTIALIAS)
    img.save(t_filepath, 'PNG')

    serialimg = f"{serial}.png"
    add_img(pathenc, serialimg)

    return serialimg


def imgfromb64(text): #data:image/png;base64,...
    text = text.replace("data:image/png;base64,", "")
    data = base64.b64decode(text)
    buf = io.BytesIO(data)
    img = Image.open(buf)
    return img

#https://stackoverflow.com/questions/44185486/generate-and-stream-compressed-file-with-flask
@app.route('/download_zip/<everything:path>', methods=['GET', 'POST'])
@cross_origin()
def download_zip(path):
    if path in vault['hash']:
        filepath = f"{metafolder}/{vault['hash'][path]}.txt"
        response = Response(yield_zip(filepath), mimetype='application/zip')
        response.headers['Content-Disposition'] = 'attachment; filename=data.zip'
        return response
    return 'no path'

def yield_zip(filepath):
    #cmd = ['cat', filepath, '|' '/usr/bin/zip', '-0', '-j', '-q', '-r', '-', '-@']
    cmd = [f'cat {filepath} | zip -0 -j -q -r - -@']
    proc = subprocess.Popen(cmd, 
                    bufsize=0, 
                    shell=True,
                    cwd=mfolder,
                    stdin=subprocess.PIPE, 
                    stdout=subprocess.PIPE)

    try:
        while True:
            buf = proc.stdout.read(4096)
            if len(buf) == 0:
                break
            yield buf
    finally:
        proc.wait()

@app.route('/list/<everything:path>', methods=['GET', 'POST'])
@cross_origin()
def listpath(path):
    if path in vault['hash']:
        files = open(f"{metafolder}/{vault['hash'][path]}.txt").read().split("\n")
    else:
        files = []
    return jsonify(files[::-1])

@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def main():
    return "hello world"

# gunicorn --workers=2 'app:create_app()' --bind=0.0.0.0:<port>
def create_app():
    return app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=myapp["port"], debug=True)

    #test
    #with app.test_client() as c:
    #    rs = c.get("/")
    #    print(rs.data)
