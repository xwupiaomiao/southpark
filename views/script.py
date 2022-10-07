from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from concurrent.futures import ThreadPoolExecutor
from function.unzip import savefile
from views import sockets
import subprocess

blue_script = Blueprint('blue_script', __name__, url_prefix='/script')


@blue_script.route('/', methods=['POST', 'GET'])
def sindex():
    return render_template('script.html')


@blue_script.route('/upload', methods=['POST', 'GET'])
def supload():
    if request.method == 'POST':
        logname = request.values.get('logname')
        username = session.get('user_info')
        if logname:
            condb('INSERT INTO `scriptinfo` (proname,username,ctime,stat) VALUES ("%s","%s",NOW(),3);' % (
                logname, username))
        else:
            pool = ThreadPoolExecutor(1)
            f = request.files['file']
            pool.submit(savefile, f, 'landingpagescripts/uploadfile')
    return jsonify('success')


@sockets.route('/script/websocket')
def script_socket(ws):
    condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "script";')
    message = ws.receive()
    resu = message.decode('utf-8')
    if message:
        res = subprocess.Popen(resu, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        resul = res.stdout.read().decode('utf-8')
        reserr = res.stderr.read().decode('utf-8')
        ws.send(resul + '\n<div style="color: red">错误消息：</div>' + reserr)
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "script";')
