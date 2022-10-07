from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect, Response, make_response
from function.conndb import condb
from function.auth import AD
import json

blue_home = Blueprint('blue_home', __name__)


# @blue_home.before_request
# def process_request(*args,**kwargs):
#     pass
#
#
# @blue_home.after_request
# def process_response(response):
#     request.args.get('name')
#     return response
#
#
# @blue_home.errorhandler(404)
# def not_found(*args,**kwargs):
#     return "页面不存在"


@blue_home.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        resauth = Response('success')
        user = request.form.get('username')
        password = request.form.get('password')
        if user and password:
            res, msg, userau = AD().auth(user, password)
            resauth.set_cookie('userauth', json.dumps(userau))
            if res:
                projlist = []
                authproject, authprojectall = condb(
                    'SELECT project.`name`,chinesename FROM project INNER JOIN projecttoperson ON project_id = project.`id` RIGHT JOIN person ON person_id = person.`id` WHERE username="{}";'.format(
                        user))
                for i in authprojectall:
                    projlist.append(i.get('name'))
                session['user_info'] = authproject.get('chinesename')
                session['author'] = userau
                session['project'] = projlist
                session.permanent = False
                return jsonify('success')
            return jsonify(msg)
        else:
            return jsonify('请输入用户名和密码')
    return render_template('login.html')


@blue_home.route('/chpwd', methods=['GET', 'POST'])
def chpassworld():
    if request.method == "POST":
        username = request.values.get('username')
        password = request.values.get('password')
        newpassword = request.values.get('newpassword')
        res = AD().changpwd(username, password, newpassword)
        return jsonify(res)
    return render_template('chpwd.html')


@blue_home.route('/', methods=['GET', 'POST'])
def index():
    logins = False
    if session.get('user_info'):
        logins = True
    if request.method == "POST":
        table = request.values.get('table')
        project = request.values.get('project')
        site = request.values.get('site')
        page = request.values.get('page')
        total = request.values.get('total')
        pages = (int(page) - 1) * int(total)
        if table == 'nginxlog' and project and site:
            list, list_all = condb(
                'SELECT `time_local`,`project`,`site`,`remote_addr`,`request_url`,`http_referer`,`http_ua`,`forwarded_for` FROM nginxlog WHERE `project` LIKE "%%{}%%" AND `site` = "{}" OR `remote_addr` LIKE "%%{}%%" AND `site` = "{}" ORDER BY id DESC LIMIT {},{};'.format(
                    project, site, project, site, pages, total))
            counts, countsall = condb(
                'SELECT COUNT(id) as total FROM nginxlog WHERE `project` LIKE "%%{}%%" AND `site` = "{}" OR `remote_addr` LIKE "%%{}%%" AND `site` = "{}";'.format(
                    project, site, project, site))
        elif table == 'nginxlog' and project and not site:
            list, list_all = condb(
                'SELECT `time_local`,`project`,`site`,`remote_addr`,`request_url`,`http_referer`,`http_ua`,`forwarded_for` FROM nginxlog WHERE `project` LIKE "%%{}%%" OR `remote_addr` LIKE "%%{}%%" ORDER BY id DESC LIMIT {},{};'.format(
                    project, project, pages, total))
            counts, countsall = condb(
                'SELECT COUNT(id) as total FROM nginxlog WHERE `project` LIKE "%%{}%%" OR `remote_addr` LIKE "%%{}%%";'.format(
                    project, project))
        elif table == 'nginxlog' and not project and site:
            list, list_all = condb(
                'SELECT `time_local`,`project`,`site`,`remote_addr`,`request_url`,`http_referer`,`http_ua`,`forwarded_for` FROM nginxlog WHERE `site` = "{}" ORDER BY id DESC LIMIT {},{};'.format(
                    site, pages, total))
            counts, countsall = condb('SELECT COUNT(id) as total FROM nginxlog WHERE `site` = "{}";'.format(site))
        elif table == 'nginxlog' and not project and not site:
            list, list_all = condb(
                'SELECT `time_local`,`project`,`site`,`remote_addr`,`request_url`,`http_referer`,`http_ua`,`forwarded_for` FROM nginxlog ORDER BY id DESC LIMIT {},{};'.format(
                    pages, total))
            counts, countsall = condb('SELECT COUNT(id) as total FROM nginxlog;')
        elif table == 'domain' and not project and not site:
            list, list_all = condb(
                'SELECT `site`,`url`,`username`,`message`,`ctime`,`status` FROM `domain` ORDER BY id DESC LIMIT {},{};'.format(
                    pages, total))
            counts, countsall = condb('SELECT COUNT(id) as total FROM `domain`;')
        elif table == 'advertlog' and not project and not site:
            list, list_all = condb(
                'SELECT `project`,`username`,`ctime`,`msg`,`status` FROM advertlog ORDER BY id DESC LIMIT {},{};'.format(
                    pages, total))
            counts, countsall = condb('SELECT COUNT(id) as total FROM advertlog;')
        elif table == 'layout':
            list, list_all = condb(
                'SELECT layout.`id`,desk,location,chinesename,job.`name`,job.`remark`,person.`mobile`,person.`status` FROM `{}` LEFT JOIN `person` ON layout.`pid` = person.`id` LEFT JOIN job ON person.`jid` = job.`id`;'.format(
                    table))
            counts = 1
        else:
            list, list_all = condb('SELECT * FROM `{}` ORDER BY id DESC LIMIT {},{};'.format(table, pages, total))
            counts, countsall = condb('SELECT COUNT(id) as total FROM {};'.format(table))
        return jsonify(list_all, counts)
    site, site_all = condb('SELECT `site`,`chname` FROM `siteinfo`')
    return render_template('index.html', site_all=site_all, logins=logins)


@blue_home.route('/quiz', methods=['POST', 'GET'])
def quiz():
    author = session.get('author')
    username = session.get('user_info')
    return render_template('quiz.html')


@blue_home.route('/ga', methods=['POST', 'GET'])
def ga():
    author = session.get('author')
    username = session.get('user_info')
    return render_template('ga.html')


@blue_home.route('/picturebooks', methods=['POST', 'GET'])
def picturebooks():
    author = session.get('author')
    username = session.get('user_info')
    return render_template('picturebooks.html')


@blue_home.route('/totalcvr', methods=['POST', 'GET'])
def totalcvr():
    author = session.get('author')
    username = session.get('user_info')
    return render_template('totalcvr.html')


@blue_home.route('/loginout', methods=['GET', 'POST'])
def loginout():
    if request.method == 'POST':
        resdel = make_response(redirect('/', '302'))
        resdel.delete_cookie('userauth')
        session.pop('user_info')
        return resdel
    return redirect('/')
