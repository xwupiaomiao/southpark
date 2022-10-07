from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
import subprocess
import json
import os
from function.getip import serveripaddr
from function.sshsftp import comupload
from function.upload import create_local
from settings import NEW_UP_LIST

blue_engineer = Blueprint('blue_engineer', __name__, url_prefix='/engineer')


class EngineerErr(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@blue_engineer.errorhandler(EngineerErr)
def engineer_err(e):
    return jsonify(e.to_dict()), e.status_code


@blue_engineer.route('/', methods=['POST', 'GET'])
def engineer():
    author = session.get('author')
    if author.get('manager') or author.get('engineer'):
        if request.method == 'POST':
            data = json.loads(request.values.get('data'))
            branch = data.get('branch')
            if len(session.get('project')) == 1:
                eng, eng_all = condb(
                    'SELECT project.name,engineer.commit_id,engineer.username,engineer.ctime,engineer.status FROM `engineer` LEFT OUTER JOIN project ON engineer.`pid` = project.`id` WHERE project.`name` ="{}" AND engineer.`branch` = "{}";'.format(
                        session.get('project')[0], branch
                    )
                )
                return jsonify(eng_all)
            else:
                eng, eng_all = condb(
                    'SELECT project.name,engineer.commit_id,engineer.username,engineer.ctime,engineer.status FROM `engineer` LEFT OUTER JOIN project ON engineer.`pid` = project.`id` WHERE project.`name` IN {}  AND engineer.`branch` = "{}";'.format(
                        tuple(session.get('project')), branch
                    )
                )
                return jsonify(eng_all)
        return render_template('engineer.html')
    return redirect('/')


@blue_engineer.route('/update', methods=['POST', 'GET'])
def engineerupdate():
    author = session.get('author')
    if author.get('manager') or author.get('engineer'):
        if request.method == 'POST':
            username = session.get('user_info')
            data = json.loads(request.values.get('data'))
            proga = data.get('name')
            branch = data.get('branch')
            local_branch = branch.split('/')[1]
            condb(
                'UPDATE engineer e INNER JOIN project p ON e.`pid` = p.`id` SET e.username="{}",e.ctime=NOW(),e.status=1 WHERE p.name="{}" and branch="{}";'.format(
                    username, proga, local_branch
                )
            )
            # 'cd /root/3nm-web/wakastar && git checkout dev && git fetch && git reset --hard origin/dev && git --no-pager log --pretty=format:%cn"&nbsp&nbsp"id：%H"&nbsp&nbsp"信息：%s"&nbsp&nbsp"日期：%ci HEAD -1'
            # 只有branch为origin/main时才更新本地仓库
            if branch == 'origin/main':
                res = subprocess.Popen(
                    'cd /root/3nm-web/{} && git fetch && git reset --hard {} && git --no-pager log --pretty=format:%cn"&nbsp&nbsp"id：%H"&nbsp&nbsp"信息：%s"&nbsp&nbsp"日期：%ci HEAD -1'.format(
                        proga, branch
                    ),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                )
                resul = res.stdout.read().decode('utf-8')
            if proga in NEW_UP_LIST:
                manage_ip = serveripaddr('projectManage')
                ssh = comupload(manage_ip)
                if branch == 'origin/main':
                    stdout, stderr, exit_code = ssh.exec_com(
                        'cd /root/3nm-web/{} && git fetch && git reset --hard {} && git --no-pager log --pretty=format:%cn"&nbsp&nbsp"id：%H"&nbsp&nbsp"信息：%s"&nbsp&nbsp"日期：%ci HEAD -1'.format(
                            proga, branch
                        )
                    )
                if branch == 'origin/dev':
                    stdout, stderr, exit_code = ssh.exec_com(
                        'cd /root/3nm-web/{}_dev && git fetch && git reset --hard {} && git --no-pager log --pretty=format:%cn"&nbsp&nbsp"id：%H"&nbsp&nbsp"信息：%s"&nbsp&nbsp"日期：%ci HEAD -1'.format(
                            proga, branch
                        )
                    )
                print(f'exit_code: {exit_code}')
                print(f'stdout: {stdout.decode("utf-8")}')
                print(f'stderr: {stderr}')
                resul = stdout.decode("utf-8")
                # if exit_code != 0:
                #     raise EngineerErr(
                #         '返回码不为0',
                #         status_code=500,
                #         payload={
                #             'stdout': stdout,
                #             'stderr': stdout,
                #             'exit_code': exit_code,
                #         },
                #     )
            commitid = resul.split('\n')[-1]
            condb(
                'UPDATE engineer e INNER JOIN project p ON e.`pid` = p.`id` SET e.commit_id="{}",e.ctime=NOW(),e.status=2 WHERE p.name="{}" and branch="{}";'.format(
                    commitid, proga, local_branch
                )
            )
            condb(
                'INSERT INTO `gamelog` (project,username,commit_id,environment,ctime,status) VALUES ("%s","%s","%s",2,NOW(),2);'
                % (proga, username, commitid)
            )
        print('测试环境更新')
        return jsonify('success')
    return redirect('/')


@blue_engineer.route('/create', methods=['GET', 'POST'])
def sitescreate():
    author = session.get('author')
    if author.get('manager') or author.get('engineer'):
        if request.method == 'POST':
            username = session.get('user_info')
            pool = ThreadPoolExecutor(1)
            data = json.loads(request.values.get('data'))
            proname = data.get('name')
            branch = data.get('branch')

            if proname in NEW_UP_LIST:
                res = pool.submit(create_local, proname, branch)
                try:
                    result = res.result()
                except Exception as e:
                    print(e)
            return jsonify('success')


@blue_engineer.route('/roback', methods=['POST', 'GET'])
def engineerroback():
    author = session.get('author')
    if author.get('manager') or author.get('engineer'):
        if request.method == 'POST':
            username = session.get('user_info')
            data = json.loads(request.values.get('data'))
            proga = data.get('name')
            commit_id = data.get('commit_id')
            branch = data.get('branch')
            condb(
                'UPDATE engineer e INNER JOIN project p ON e.`pid` = p.`id` SET e.username="{}",e.ctime=NOW(),e.status=1 WHERE p.name="{}";'.format(
                    username, proga
                )
            )
            res = subprocess.Popen(
                'cd /root/3nm-web/{} && git checkout {} && git fetch && git reset --hard {} && git --no-pager log --pretty=format:%cn"&nbsp&nbsp"id：%H"&nbsp&nbsp"信息：%s"&nbsp&nbsp"日期：%ci HEAD -1'.format(
                    proga, branch, commit_id
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )
            if proga in NEW_UP_LIST:
                manage_ip = serveripaddr('projectManage')
                ssh = comupload(manage_ip)
                stdout, stderr, exit_code = ssh.exec_com(
                    'cd /root/3nm-web/{} && git checkout {} && git fetch && git reset --hard {} && git --no-pager log --pretty=format:%cn"&nbsp&nbsp"id：%H"&nbsp&nbsp"信息：%s"&nbsp&nbsp"日期：%ci HEAD -1'.format(
                        proga, branch, commit_id
                    )
                )
                print(f'rollback {exit_code}')
            resul = res.stdout.read().decode('utf-8')
            reserr = res.stderr.read().decode('utf-8')
            if 'fatal' in reserr:
                condb(
                    'UPDATE engineer e INNER JOIN project p ON e.`pid` = p.`id` SET e.username="{}",e.ctime=NOW(),e.status=4 WHERE p.name="{}";'.format(
                        username, proga
                    )
                )
                return jsonify('commit_id错误，请检查')
            commitid = resul.split('\n')[-1]
            condb(
                'UPDATE engineer e INNER JOIN project p ON e.`pid` = p.`id` SET e.commit_id="{}",e.ctime=NOW(),e.status=3 WHERE p.name="{}";'.format(
                    commitid, proga
                )
            )
            condb(
                'INSERT INTO `gamelog` (project,username,commit_id,environment,ctime,status) VALUES ("%s","%s","%s",2,NOW(),3);'
                % (proga, username, commit_id)
            )
            print('测试环境回退')
            return jsonify('success')
    return redirect('/')
