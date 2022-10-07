from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from concurrent.futures import ThreadPoolExecutor
from function.advertcheck import check_ads_sucai, uploadadvert
from function.unzip import saveadvert
import json, os

blue_advert = Blueprint('blue_advert', __name__, url_prefix='/advert')


@blue_advert.route('/', methods=['POST', 'GET'])
def advert():
    author = session.get('author')
    if author.get('manager') or author.get('advert'):
        if request.method == 'POST':
            if len(session.get('project')) == 1:
                resa, resall = condb(
                    'SELECT `name`,`username`,advert.`ctime`,advert.`lock`,advert.`status` FROM `advert` INNER JOIN project ON advert.`pid`= project.`id` WHERE `name` ="{}";'.format(
                        session.get('project')[0]))
                return jsonify(resall)
            else:
                resa, resall = condb(
                    'SELECT `name`,`username`,advert.`ctime`,advert.`lock`,advert.`status` FROM `advert` INNER JOIN project ON advert.`pid`= project.`id` WHERE `name` IN {};'.format(
                        tuple(session.get('project'))))
                return jsonify(resall)
        return render_template('advert.html', project_list=session.get('project'))
    return redirect('/')


@blue_advert.route('/upload', methods=['POST', 'GET'])
def advertupload():
    username = session.get('user_info')
    author = session.get('author')
    if author.get('manager') or author.get('advert'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "advert"')
            project = request.values.get('project')
            pool = ThreadPoolExecutor(1)
            if request.values.get('advert') == 'upload':
                pool.submit(uploadadvert, username, project)
                return jsonify('success')
            else:
                project = request.values.get('project')
                f = request.files['file']
                pool.submit(saveadvert, f, 'advert/file/{}'.format(project))
                return jsonify('success')
    return redirect('/')


@blue_advert.route('/check', methods=['POST', 'GET'])
def advertcheck():
    author = session.get('author')
    if author.get('manager') or author.get('advert'):
        if request.method == 'POST':
            project = request.values.get('project')
            rescheck = check_ads_sucai('advert/file/{}'.format(project))
            if rescheck == 0:
                return jsonify({'status': 0, 'message': "all things ready"})
            else:
                os.system('rm -fr advert/file/{}/*'.format(project))
                return jsonify({'status': -1, 'message': rescheck})
    return redirect('/')


@blue_advert.route('/delete', methods=['POST', 'GET'])
def advertdelete():
    author = session.get('author')
    if author.get('manager') or author.get('advert'):
        if request.method == 'POST':
            project = request.values.get('project')
            os.system('rm -fr advert/file/{}/*'.format(project))
            return jsonify('success')
    return redirect('/')
