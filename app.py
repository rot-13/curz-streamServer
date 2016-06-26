from flask import Flask
from flask import request
from werkzeug.utils import secure_filename
from flask_sockets import Sockets
import os

HOST = 'https://cpc-curz.herokuapp.com/'
PORT = 443
UPLOAD_PATH = 'static/audio/'
UPLOAD_FOLDER = './%s' % (UPLOAD_PATH)
ALLOWED_EXTENSIONS = set(['m4a', 'mp3'])

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
sockets = Sockets(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

speakers = list()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@sockets.route('/connect')
def connect_socket(ws):
    speakers.append(ws)
    print 'connected'
    while not ws.closed:
        message = ws.receive()
        ws.send(message)


def get_file_url(filename):
    file_url = 'http://%s:%s/%s%s' % (HOST, PORT, UPLOAD_PATH, filename)
    return file_url


def broadcast_file(file_url):
    for speaker in speakers:
        if not speaker.closed:
            speaker.send(file_url)


@app.route('/play_url', methods=['POST'])
def play_url():
    file_url = request.form['url']
    broadcast_file(file_url)
    return 'playing: ' + file_url


@app.route('/play_file', methods=['POST'])
def play_file():
    if 'file' not in request.files:
        return 'No file found'
    received_file = request.files['file']
    if received_file and allowed_file(received_file.filename):
        filename = secure_filename(received_file.filename)
        received_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_url = get_file_url(filename)
        broadcast_file(file_url)
        return 'playing: ' + file_url

if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', PORT), app, handler_class=WebSocketHandler)
    server.serve_forever()
