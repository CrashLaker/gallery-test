from flask import Flask, request, jsonify, json, abort, redirect, url_for, render_template, send_file
from flask_cors import CORS, cross_origin
import os
import re
import subprocess
import traceback
import base64
import json
import uuid
import re
import io
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

folder = "./imgs/"
tfolder = f"{folder}/thumbs/"
mfolder = f"{folder}/main/"
metafolder = "./meta/"
for f2 in [folder, tfolder, mfolder, metafolder]:
    if not os.path.exists(f2):
        os.mkdir(f2)
datatrack = "track.json"
if not os.path.exists(datatrack):
    vault = {"hash": {}, "rev": {}}
else:
    with open(datatrack) as f:
        vault = json.load(f)


def get_serial():
    return uuid.uuid4().hex

def save_vault():
    with open(datatrack, "w") as f:
        json.dump(vault, f)

def load_json(filepath):
    with open(filepath) as f:
        data = json.load(f)
    return data

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
        metapath = f"{metafolder}/{serial}.json"
        with open(metapath, 'w') as f:
            json.dump([], f)
        vault['hash'][path] = serial
        vault['rev'][serial] = path
        save_vault()
    else:
        serial = vault['hash'][path]
    return serial

def add_img(pathenc, serialimg):
    filepath = f"{metafolder}/{pathenc}.json"
    with open(filepath) as f:
        data = json.load(f)
    data.append(serialimg)
    with open(filepath, 'w') as f:
        json.dump(data, f)


@app.route('/thumb/<img>', methods=['GET'])
@cross_origin()
def thumb(img):
    lfolder = tfolder
    filepath = f"{lfolder}/{img}"
    if os.path.exists(filepath): 
        return send_file(filepath)
    return ""

@app.route('/img/<img>', methods=['GET'])
@cross_origin()
def img(img):
    lfolder = mfolder
    filepath = f"{lfolder}/{img}"
    if os.path.exists(filepath): 
        return send_file(filepath)
    return ""

@app.route('/recv', methods=['GET', 'POST'])
@cross_origin()
def recv():
    req = request.json

    if not 'image64' in req:
        return 'nothing'

    image = req['image64']
    path = req['path']
    print(path)
    print(image[:30])
    pathenc = validate_path(path)

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


@app.route('/list/<everything:path>', methods=['GET', 'POST'])
@cross_origin()
def listpath(path):
    if path in vault['hash']:
        files = load_json(f"{metafolder}/{vault['hash'][path]}.json")
    else:
        files = []
    return jsonify(files)

@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def main():
    return "hello world"

# gunicorn --workers=2 'app:create_app()' --bind=0.0.0.0:<port>
def create_app():
    return app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)
    
    #test 
    #with app.test_client() as c:
    #    rs = c.get("/")
    #    print(rs.data)
