from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from concurrent.futures import ThreadPoolExecutor
from function.report import reports
from function.upload import (
    up,
    roback,
    create,
    up_data,
    up_manage,
    create_manage,
    create_local,
)
import json
import time
from settings import NEW_UP_LIST

blue_sites = Blueprint('blue_sites', __name__, url_prefix='/sites')


@blue_sites.route('/', methods=['GET', 'POST'])
def sites():
    author = session.get('author')
    if author.get('manager') or author.get('upload'):
        if request.method == 'POST':
            project_list = request.values.getlist('project')
            if request.values.get('zoneinfo_id'):
                zoneinfo_id = request.values.get('zoneinfo_id')
                resupload, resuploadall = condb(
                    'SELECT site,chname FROM domainzone INNER JOIN siteinfo ON sid = siteinfo.`id` INNER JOIN zoneinfo ON zid = zoneinfo.`id` WHERE zoneinfo.`id`="{}";'.format(
                        zoneinfo_id
                    )
                )
                return jsonify(resuploadall)
            if len(request.values.getlist('project')) == 1:
                resupload, resuploadall = condb(
                    'SELECT `user`,`name`,`url`,`ctime`,`sendsize`,`percent`,`status`,`lock`,`rolback`,`zone`,`zoneinfo_id`,`forbiden` FROM `project` INNER JOIN zoneinfo ON project.`zoneinfo_id` = zoneinfo.`id` WHERE `name` ="{}";'.format(
                        project_list[0]
                    )
                )
                return jsonify(resuploadall)
            else:
                resupload, resuploadall = condb(
                    'SELECT `user`,`name`,`url`,`ctime`,`sendsize`,`percent`,`status`,`lock`,`rolback`,`zone`,`zoneinfo_id`,`forbiden` FROM `project` INNER JOIN zoneinfo ON project.`zoneinfo_id` = zoneinfo.`id` WHERE `name` IN {};'.format(
                        tuple(project_list)
                    )
                )
                return jsonify(resuploadall)
        return render_template('sites.html', project_list=session.get('project'))
    return redirect('/')


@blue_sites.route('/create', methods=['GET', 'POST'])
def sitescreate():
    author = session.get('author')
    if author.get('manager') or author.get('upload'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "sites";')
            username = session.get('user_info')
            pool = ThreadPoolExecutor(1)
            project_list = request.values.getlist('project')
            for proname in project_list:
                procheck, procheckall = condb(
                    'SELECT `name`,`lock` FROM project WHERE `name` = "{}";'.format(
                        proname
                    )
                )
                if not procheck.get('lock'):
                    condb(
                        'UPDATE `project` SET `user`="{}",`status` = NULL,`lock`=1,`ctime` = NOW(), `rolback` = NULL WHERE `name` = "{}";'.format(
                            username, proname
                        )
                    )
                    if proname in NEW_UP_LIST:
                        res = pool.submit(create_local, proname)
                        try:
                            result = res.result()
                        except Exception as e:
                            print(e)
                            condb(
                                'UPDATE `project` SET `status` = 4,`ctime` = NOW(),`lock`=NULL,`sendsize`=NULL,`percent`=NULL WHERE `name`="{}";'.format(
                                    proname
                                )
                            )
                            condb(
                                'UPDATE `splock` SET `lock` = NULL WHERE `function` = "sites";'
                            )
                    else:
                        pool.submit(create, proname)
            return jsonify('success')


@blue_sites.route('/upload', methods=['GET', 'POST'])
def sitesupload():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('upload'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "sites";')
            pool = ThreadPoolExecutor(2)
            pro_list = request.values.getlist('projectname')
            for pro in pro_list:
                procheck, procheckall = condb(
                    'SELECT `name`,`lock` FROM project WHERE `name` = "{}";'.format(pro)
                )
                if not procheck.get('lock'):
                    condb(
                        'UPDATE `project` SET `user`="{}",`lock`=1 WHERE `name`="{}";'.format(
                            username, pro
                        )
                    )
                    reports(
                        "用户：{}".format(username),
                        "站点：{}，开始上线".format(pro),
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    if pro in NEW_UP_LIST:
                        res = pool.submit(up_manage, pro, username)
                        try:
                            result = res.result()
                        except Exception as e:
                            condb(
                                'UPDATE `splock` SET `lock` = NULL WHERE `function` = "sites";'
                            )
                            condb(
                                'UPDATE `project` SET `user`="{}",`status` = 2,`lock`=NULL WHERE `name`="{}";'.format(
                                    username, pro
                                )
                            )
                            reports(
                                "用户：{}".format(username),
                                "站点：{}，上线失败".format(pro),
                                time.strftime("%Y-%m-%d %H:%M:%S"),
                            )
                    else:
                        pool.submit(up, pro, username)
                    return jsonify('success')
                else:
                    return jsonify(False)
    return redirect('/')


@blue_sites.route('/roback', methods=['GET', 'POST'])
def sitesroback():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('upload'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "sites";')
            proname = request.values.get('name')
            reports(
                "用户：{}".format(username),
                "站点：{}，开始回退".format(proname),
                time.strftime("%Y-%m-%d %H:%M:%S"),
            )
            roback(proname, username)
            reports(
                "用户：{}".format(username),
                "站点：{}，回退完成".format(proname),
                time.strftime("%Y-%m-%d %H:%M:%S"),
            )
            condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "sites";')
            return jsonify('success')
    return redirect('/')
