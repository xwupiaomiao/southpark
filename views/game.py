from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from function.sshsftp import comupload
from function.getip import serveripaddr, serverip, getserverip, serveripid
import subprocess
import json

blue_game = Blueprint('blue_game', __name__, url_prefix='/game')


@blue_game.route('/', methods=['GET', "POST"])
def game():
    author = session.get('author')
    if author.get('manager') or author.get('game'):
        if request.method == 'POST':
            if request.values.get('select') == 'modules':
                res, resall = condb('SELECT * FROM modules;')
                return jsonify(resall)
            elif request.values.get('select') == 'resources':
                gamelist, gamelistall = condb(
                    'SELECT resources.`id`,resources.`name`,resources.`design`,resources.`description`,resources.`ctime`,modules.`name` FROM resources INNER JOIN modules ON `mid` = modules.`id` ORDER BY id DESC;')
                return jsonify(gamelistall)
            elif request.values.get('select') == 'url':
                modulesname = request.values.get('modules')
                res, resall = condb(
                    'SELECT resources.`name` FROM resources INNER JOIN modules ON `mid` = modules.`id` WHERE modules.`name`="{}";'.format(
                        modulesname))
                return jsonify(resall)
            elif request.values.get('select') == 'project':
                zoneinfo_id = request.values.get('zoneinfo_id')
                if zoneinfo_id:
                    res, resall = condb(
                        'SELECT url,site,chname FROM project INNER JOIN zoneinfo ON zoneinfo_id=zoneinfo.`id` INNER JOIN domainzone ON domainzone.`zid`=zoneinfo.`id` INNER JOIN siteinfo ON domainzone.`sid` = siteinfo.`id` WHERE zoneinfo.`id`="{}";'.format(
                            zoneinfo_id))
                else:
                    res, resall = condb(
                        'SELECT `name`,`zoneinfo_id` FROM project ;')
                return jsonify(resall)
            elif request.values.get('select') == 'server':
                res, resall = condb(
                    'SELECT id,sname FROM `server` WHERE sname NOT IN ("publicgame","gamevideo","toyvideo","image","animationvideo");')
                return jsonify(resall)
            list, list_all = condb('SELECT * FROM `game` INNER JOIN `server` ON sid = server.`id`;')
            return jsonify(list_all)
        return render_template('game.html')
    return redirect('/')


@blue_game.route('/update', methods=['GET', "POST"])
def gameupdate():
    author = session.get('author')
    if author.get('manager') or author.get('game'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "game";')
            username = session.get('user_info')
            data = json.loads(request.values.get('data'))
            serverid = data.get('project')
            commit_id = data.get('commit_id')
            environment = data.get('environment')
            branch = data.get('branch')
            msg = data.get('msg')
            serveripa, servername = serveripid(serverid)
            if environment == 1 and commit_id == 'update':
                ssh = comupload(serveripa)
                condb(
                    'UPDATE `game` SET `username`="{}",`ctime` = NOW(),`status` = 1 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        username, serverid, environment))
                resul, reserr = ssh.comand(
                    'cd /var/www/html/game && git fetch && git reset --hard {} && git rev-parse HEAD'.format(
                        branch))
                ssh.sshclose()
                commitid = resul.split('\n')[-2]
                condb(
                    'UPDATE `game` SET `commit_id`="{}",`ctime` = NOW(),`status` = 2 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        commitid, serverid, environment))
                condb(
                    'INSERT INTO `gamelog` (project,username,commit_id,environment,ctime,status) VALUES ("%s","%s","%s","%s",NOW(),2);' % (
                        servername, username, commitid, environment))
                print('线上正式环境更新')
            elif environment == 0 and commit_id == 'update':
                condb(
                    'UPDATE `game` SET `username`="{}",`ctime` = NOW(),`status` = 1 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        username, serverid, environment))
                res = subprocess.Popen(
                    'cd /root/3nm-web/site/game/{}/game && git fetch && git reset --hard {} && git rev-parse HEAD'.format(
                        servername, branch), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                resul = res.stdout.read().decode('utf-8')
                commitid = resul.split('\n')[-2]
                condb(
                    'UPDATE `game` SET `commit_id`="{}",`ctime` = NOW(),`status` = 2 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        commitid, serverid, environment))
                condb(
                    'INSERT INTO `gamelog` (project,username,commit_id,environment,ctime,status) VALUES ("%s","%s","%s","%s",NOW(),2);' % (
                        servername, username, commitid, environment))
                print('测试环境更新')
            elif environment == 0 and commit_id == 'push':
                condb(
                    'UPDATE `game` SET `username`="{}",`ctime` = NOW(),`status` = 1 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        username, serverid, environment))
                res = subprocess.Popen(
                    'cd /root/3nm-web/site/game/{}/game && git add . && git commit -m "{}" && git push origin HEAD:main && git rev-parse HEAD'.format(
                        servername, msg), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                resul = res.stdout.read().decode('utf-8')
                commitid = resul.split('\n')[-2]
                condb(
                    'UPDATE `game` SET `commit_id`="{}",`ctime` = NOW(),`status` = 2 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        commitid, serverid, environment))
                condb(
                    'INSERT INTO `gamelog` (project,username,commit_id,environment,ctime,status) VALUES ("%s","%s","%s","%s",NOW(),2);' % (
                        servername, username, commitid, environment))
                print('测试环境推送')
            condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "game";')
            return jsonify('success')
    return redirect('/')


@blue_game.route('/roback', methods=['GET', "POST"])
def gameroback():
    author = session.get('author')
    if author.get('manager') or author.get('game'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "game";')
            username = session.get('user_info')
            data = json.loads(request.values.get('data'))
            serverid = data.get('project')
            commit_id = data.get('commit_id')
            environment = data.get('environment')
            branch = data.get('branch')
            serveripa, servername = serveripid(serverid)
            if environment == 1:
                ssh = comupload(serveripa)
                condb(
                    'UPDATE `game` SET `username`="{}",`ctime` = NOW(),`status` = 1 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        username, serverid, environment))
                resul, reserr = ssh.comand(
                    'cd /var/www/html/game && git checkout {} && git fetch && git reset --hard {} && git rev-parse HEAD'.format(
                        branch, commit_id))
                ssh.sshclose()
                if 'fatal' in reserr:
                    condb(
                        'UPDATE `game` SET `username`="{}",`ctime` = NOW(),`status` = 4 WHERE `sid`="{}" AND `environment`="{}";'.format(
                            username, serverid, environment))
                    return jsonify('commit_id错误，请检查')
                commitid = resul.split('\n')[-2]
                condb(
                    'UPDATE `game` SET `commit_id`="{}",`ctime` = NOW(),`status` = 3 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        commitid, serverid, environment))
                condb(
                    'INSERT INTO `gamelog` (project,username,commit_id,environment,ctime,status) VALUES ("%s","%s","%s","%s",NOW(),3);' % (
                        servername, username, commit_id, environment))
                print('线上正式环境回退')
            elif environment == 0:
                condb(
                    'UPDATE `game` SET `username`="{}",`ctime` = NOW(),`status` = 1 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        username, serverid, environment))
                res = subprocess.Popen(
                    'cd /root/3nm-web/site/game/{}/game && git checkout {} && git fetch && git reset --hard {} && git rev-parse HEAD'.format(
                        servername, branch, commit_id), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                resul = res.stdout.read().decode('utf-8')
                reserr = res.stderr.read().decode('utf-8')
                if 'fatal' in reserr:
                    condb(
                        'UPDATE `game` SET `username`="{}",`ctime` = NOW(),`status` = 4 WHERE `sid`="{}" AND `environment`="{}";'.format(
                            username, serverid, environment))
                    return jsonify('commit_id错误，请检查')
                commitid = resul.split('\n')[-2]
                condb(
                    'UPDATE `game` SET `commit_id`="{}",`ctime` = NOW(),`status` = 3 WHERE `sid`="{}" AND `environment`="{}";'.format(
                        commitid, serverid, environment))
                condb(
                    'INSERT INTO `gamelog` (project,username,commit_id,environment,ctime,status) VALUES ("%s","%s","%s","%s",NOW(),3);' % (
                        servername, username, commit_id, environment))
                print('测试环境回退')
            condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "game";')
            return jsonify('success')
    return redirect('/')


@blue_game.route('/addgame', methods=['GET', "POST"])
def addgame():
    author = session.get('author')
    if author.get('manager') or author.get('game'):
        if request.method == 'POST':
            username = session.get('user_info')
            project = request.values.get('servername')
            environment = request.values.get('environment')
            githuburl = request.values.get('githuburl')
            pubgithuburl = request.values.get('pubgithuburl')
            serveripaddress, projectname = getserverip(project)
            if environment:
                if githuburl:
                    githubdir = githuburl.split('/')[1].split('.')[0]
                    sshclient = comupload(serveripaddress)
                    resul, reserr = sshclient.comand(
                        'if [[ ! -d /var/www/html/game/{project} ]]; then mkdir /var/www/html/game/{project};fi && cd /var/www/html/game/{project} && git clone {github} && mv {githubdir} game && git rev-parse HEAD'.format(
                            project=projectname, github=githuburl, githubdir=githubdir))
                    commitid = resul.split('\n')[-2]
                    sshclient.sshclose()
                    condb(
                        'INSERT INTO `game` (commit_id,username,environment,ctime,status,sid) VALUES ("%s","%s","%s",NOW(),NULL,"%s");' % (
                            commitid, username, environment, project))
                if pubgithuburl:
                    pubgithuburldir = pubgithuburl.split('/')[1].split('.')[0]
                    sshclient = comupload(serveripaddress)
                    resulpub, reserrpub = sshclient.comand(
                        'cd /var/www/html && git clone {github} && mv {githubdir} game && git rev-parse HEAD'.format(
                            github=pubgithuburl, githubdir=pubgithuburldir))
                    commitidpub = resulpub.split('\n')[-2]
                    sshclient.sshclose()
                    condb(
                        'INSERT INTO `game` (commit_id,username,environment,ctime,status,sid) VALUES ("%s","%s","%s",NOW(),NULL,"%s");' % (
                            commitidpub, username, environment, project))
                condb(
                    'INSERT INTO `game` (commit_id,username,environment,ctime,status,sid) VALUES (NULL,"%s","%s",NOW(),NULL,"%s");' % (
                        username, environment, project))
            else:
                res = subprocess.Popen(
                    'if [[ ! -d /var/www/html/game/{project} ]]; then mkdir -p /var/www/html/game/{project};fi && cd /root/3nm-web/site/game/{project} && git clone {github} && mv {githubdir} game && git rev-parse HEAD'.format(
                        project=projectname, github=githuburl, githubdir=githuburl.split('/')[1].split('.')[0]),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, shell=True)
                resul = res.stdout.read().decode('utf-8')
                commitid = resul.split('\n')[-2]
                condb(
                    'INSERT INTO `game` (commit_id,username,environment,ctime,status,sid) VALUES ("%s","%s","%s",NOW(),NULL,"%s");' % (
                        commitid, username, environment, project))
            return jsonify('success')
    return redirect('/')


@blue_game.route('/addmodules', methods=['GET', "POST"])
def gameaddmodules():
    author = session.get('author')
    if author.get('manager') or author.get('game'):
        if request.method == 'POST':
            mid = request.values.get('mid')
            name = request.values.get('name')
            developer = request.values.get('developer')
            remark = request.values.get('remark')
            if mid:
                condb(
                    'UPDATE `modules` SET `name` = "{}",developer="{}",description="{}",`ctime` = NOW() WHERE `id`="{}";'.format(
                        name, developer, remark, mid))
                return jsonify('success')
            else:
                modulesname, modulesnameall = condb('SELECT id FROM modules WHERE `name`="{}";'.format(name))
                if modulesname:
                    return jsonify(False)
                else:
                    condb(
                        'INSERT INTO `modules` (`name`,developer,description,ctime) VALUES ("%s","%s","%s",NOW());' % (
                            name, developer, remark))
                    return jsonify('success')
    return redirect('/')


@blue_game.route('/addresouces', methods=['GET', "POST"])
def gameaddresouces():
    author = session.get('author')
    if author.get('manager') or author.get('game'):
        if request.method == 'POST':
            rid = request.values.get('rid')
            mid = request.values.get('mid')
            name = request.values.get('name')
            design = request.values.get('design')
            remark = request.values.get('remark')
            if rid:
                condb(
                    'UPDATE `resources` SET `name` = "{}",design="{}",description="{}",`ctime` = NOW(),mid="{}" WHERE `id`="{}";'.format(
                        name, design, remark, mid, rid))
                return jsonify('success')
            else:
                resouces, ressoucesall = condb(
                    'SELECT id FROM resources WHERE mid="{}" AND `name`="{}";'.format(mid, name))
                if resouces:
                    return jsonify(False)
                else:
                    condb(
                        'INSERT INTO `resources` (`name`,design,description,ctime,mid) VALUES ("%s","%s","%s",NOW(),"%s");' % (
                            name, design, remark, mid))
                return jsonify('success')
    return redirect('/')
