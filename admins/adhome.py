from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from views import sockets
import subprocess
import json, os, time

blue_adhome = Blueprint('blue_adhome', __name__, url_prefix='/admin')


@blue_adhome.route('/', methods=['POST', 'GET'])
def admin():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            table = request.values.get('table')
            list, list_all = condb(
                'SELECT * FROM `{}` ;'.format(table))
            return jsonify(list_all)
        return render_template('admin/index.html')
    return redirect('/')


@blue_adhome.route('/upsppage', methods=['POST', 'GET'])
def adminupsppage():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            username = session.get('user_info')
            data = json.loads(request.values.get('data'))
            branch = data.get('branch')
            res = subprocess.Popen(
                'cd /root/southpark/templates && git fetch && git reset --hard {} && git rev-parse HEAD'.format(
                    branch), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            resul = res.stdout.read().decode('utf-8')
            commitid = resul.split('\n')[-2]
            condb('UPDATE adminsp SET username="{}",pagecommit="{}",ctime=NOW(),status=2 WHERE id=1;'.format(
                username, commitid))
            return jsonify('success')
    return redirect('/')


@blue_adhome.route('/rosppage', methods=['POST', 'GET'])
def adminrosppage():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            username = session.get('user_info')
            data = json.loads(request.values.get('data'))
            branch = data.get('branch')
            commit_id = data.get('commit_id')
            res = subprocess.Popen(
                'cd /root/southpark/templates && git checkout {} && git fetch && git reset --hard {} && git rev-parse HEAD'.format(
                    branch, commit_id), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            resul = res.stdout.read().decode('utf-8')
            reserr = res.stderr.read().decode('utf-8')
            if 'fatal' in reserr:
                condb(
                    'UPDATE adminsp SET username="{}",ctime=NOW(),status=4 WHERE id=1;'.format(
                        username))
                return jsonify('commit_id错误，请检查')
            commitid = resul.split('\n')[-2]
            condb('UPDATE adminsp SET username="{}",pagecommit="{}",ctime=NOW(),status=3 WHERE id=1;'.format(
                username, commitid))
            return jsonify('success')
    return redirect('/')


@blue_adhome.route('/spreload', methods=['POST', 'GET'])
def adminspreload():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager'):
        if request.method == 'POST':
            engrel, engrelall = condb('SELECT `name`,`lock` FROM splock;')
            spstatus = []
            for i in engrelall:
                if i.get('lock'):
                    spstatus.append(i.get('name'))
            if spstatus:
                return jsonify(spstatus)
            else:
                os.system('echo \\"Reload {} $(date +%F_%T)\\" >>uwsgi/reload'.format(username))
                return jsonify('success')
    return redirect('/')


@blue_adhome.route('/spchange', methods=['POST', 'GET'])
def adminspchange():
    username = session.get('user_info')
    author = session.get('author')
    if author.get('manager'):
        res = subprocess.Popen(
            'cd /root/southpark/ && git pull && git rev-parse HEAD', stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True)
        resul = res.stdout.read().decode('utf-8')
        commitid = resul.split('\n')[-2]
        print(resul)
        condb('UPDATE adminsp SET admincommit="{}" WHERE id=1;'.format(commitid))
        os.system('echo \\"Change {} $(date +%F_%T)\\" >>uwsgi/change'.format(username))
        return jsonify('success')
    return redirect('/')


@blue_adhome.route('/uwsgi', methods=['POST', 'GET'])
def uwsgi():
    author = session.get('author')
    if author.get('manager'):
        return render_template('admin/uwsgi.html')
    return redirect('/')


@sockets.route('/admin/websocket')
def uwsgilog(ws):
    with open('/var/log/uwsgi.log', 'r', encoding='utf-8') as f:
        for line in f:
            ws.send(line + '</br>')
            time.sleep(0.03)


@blue_adhome.route('/addserver', methods=['POST', 'GET'])
def addserver():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            username = session.get('user_info')
            sname = request.values.get('sname')
            ipaddress = request.values.get('ip')
            remark = request.values.get('remark')
            condb('INSERT INTO `server` (`username`,`sname`,ip,ctime,remark) VALUES ("%s","%s","%s",NOW(),"%s");' % (
                username, sname, ipaddress, remark))
            return jsonify('success')
    return redirect('/')


@blue_adhome.route('/editserver', methods=['POST', 'GET'])
def editserver():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            username = session.get('user_info')
            sid = request.values.get('id')
            sname = request.values.get('sname')
            ipaddress = request.values.get('ip')
            remark = request.values.get('remark')
            condb('UPDATE `server` SET username="{}",sname="{}",ip="{}",ctime=NOW(),remark="{}" WHERE id="{}";'.format(
                username, sname, ipaddress, remark, sid))
            return jsonify('success')
    return redirect('/')
