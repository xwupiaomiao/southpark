from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from concurrent.futures import ThreadPoolExecutor
from function.upvideo import uptoyvideo, savevideo, upanvideo
import json

blue_video = Blueprint('blue_video', __name__, url_prefix='/video')


@blue_video.route('/', methods=['POST', 'GET'])
def video():
    author = session.get('author')
    if author.get('manager') or author.get('video'):
        if request.method == 'POST':
            if request.values.get('table') == 'video':
                page = request.values.get('page')
                total = request.values.get('total')
                pages = (int(page) - 1) * int(total)
                resvideo, resvideoall = condb(
                    'SELECT video.`id`,title,category,tag,username,testurl,ctime,`status`,cat FROM `video` INNER JOIN videocat ON cat_id=videocat.`id` ORDER BY video.`id` DESC LIMIT {},{};'.format(
                        pages, total))
                counts, countsall = condb(
                    'SELECT COUNT(video.`id`) as total FROM `video` INNER JOIN videocat ON cat_id=videocat.`id` ORDER BY video.`id`;')
                return jsonify(resvideoall, counts)
            elif request.values.get('table') == 'zoneinfo':
                reszone, reszoneall = condb('SELECT id,`zone` FROM `zoneinfo`;')
                return jsonify(reszoneall)
            elif request.values.get('table') == 'videocat':
                reszone, reszoneall = condb('SELECT id,`cat` FROM `videocat`;')
                return jsonify(reszoneall)
    return render_template('video.html')


@blue_video.route('/upload', methods=['POST', 'GET'])
def uploadvido():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('video'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "video";')
            pool = ThreadPoolExecutor(1)
            if request.values.get('select') == 'data':
                data = json.loads(request.values.get('data'))
                script = data.get('script')
                filename = data.get('filename')
                videoinfo = data.get('data')
                zipname = data.get('zipname')
                site = data.get('site')
                if site == 1:
                    pool.submit(uptoyvideo, script, filename, videoinfo, zipname, username)
                elif site == 2:
                    pool.submit(upanvideo, script, filename, videoinfo, zipname, username)
                return jsonify('success')
            else:
                f = request.files['file']
                pool.submit(savevideo, f, '../video/upload')
                return jsonify('success')
    return redirect('/')
