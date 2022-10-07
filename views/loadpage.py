from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from concurrent.futures import ThreadPoolExecutor
from function.unzip import imagetobase
import json, os

blue_loadpage = Blueprint('blue_loadpage', __name__, url_prefix='/loadpage')


@blue_loadpage.route('/', methods=['POST', 'GET'])
def loadpage():
    author = session.get('author')
    if author.get('manager') or author.get('loadpage'):
        if request.method == 'POST':
            if request.values.get('select') == 'gamesinfo':
                games, gamesall = condb('SELECT `id`,`title`,`test_url`,`modules`,`resources` FROM `gamelist`;')
                return jsonify(gamesall)
            elif request.values.get('select') == 'project':
                if len(session.get('project')) == 1:
                    loadname, loadnameall = condb(
                        'SELECT `id`,`name` FROM project WHERE `name` = "{}";'.format(session.get('project')[0]))
                    return jsonify(loadnameall)
                else:
                    loadname, loadnameall = condb(
                        'SELECT `id`,`name` FROM project WHERE `name` IN {};'.format(tuple(session.get('project'))))
                    return jsonify(loadnameall)
            elif request.values.get('select') == 'templates':
                tempate, tempateall = condb('SELECT * FROM `templates`;')
                return jsonify(tempateall)
            elif request.values.get('select') == 'loadpage':
                pid = request.values.get('pid')
                htmlpage = request.values.get('htmlpage')
                if request.values.get('selectone') == 'one':
                    updateselect, updateselectall = condb(
                        'SELECT coverlist FROM `loadpage` WHERE htmlpage="{}" AND pid="{}";'.format(
                            htmlpage, pid))
                    # 备份coverlist字段
                    condb(
                        'UPDATE `loadpage` SET `coverlistbak`="{}" WHERE htmlpage="{}" AND pid="{}";'.format(
                            updateselect.get('coverlist'), htmlpage, pid))
                    if updateselect:
                        resall = []
                        for i in json.loads(updateselect.get('coverlist')):
                            resselect, resselectall = condb(
                                'SELECT id,imagename,cover,imageformat,ginfo_id FROM imagecover WHERE id="{}";'.format(
                                    i))
                            resall.append(resselect)
                        return jsonify(resall)
                    else:
                        return jsonify('{},不存在'.format(htmlpage))
                else:
                    updateselect, updateselectall = condb(
                        'SELECT id,htmlpage,tempid FROM `loadpage` WHERE htmlpage LIKE "%%{}%%" AND pid="{}";'.format(
                            htmlpage, pid))
                    return jsonify(updateselectall)
            elif request.values.get('select') == 'image':
                imageid = request.values.get('id')
                proname = []
                chimagcovall, chimagcov = condb(
                    'SELECT gamelist.id,test_url,resources,project.`id`,project.`name` FROM `imageproject` INNER JOIN `imagecover` ON `imageproject`.iid = `imagecover`.id INNER JOIN `project` ON `imageproject`.pid=`project`.id INNER JOIN `gamelist` ON imagecover.`ginfo_id`= gamelist.`id` WHERE imagecover.`id`="{}";'.format(
                        imageid))
                if chimagcov:
                    for i in chimagcov:
                        proname.append(i.get('project.id'))
                        i.pop('project.id')
                        i.pop('name')
                    chimagcov = chimagcov[0]
                    chimagcov['project'] = proname
                else:
                    chimagcov, chimagcovall = condb(
                        'SELECT gamelist.id,test_url,resources FROM `imagecover` INNER JOIN `gamelist` ON imagecover.`ginfo_id`= gamelist.`id` WHERE imagecover.`id`="{}";'.format(
                            imageid))
                return jsonify(chimagcov)
            elif request.values.get('select') == 'check':
                pid = request.values.get('pid')
                htmlpage = request.values.get('htmlpage')
                htmlpageone, htmlpageall = condb(
                    'SELECT * FROM `loadpage` WHERE htmlpage="{}" AND pid="{}";'.format(htmlpage, pid))
                if htmlpageone:
                    return jsonify(False)
                else:
                    return jsonify(True)
            elif request.values.get('select') == 'search':
                use = request.values.get('use')
                gamename = request.values.get('gamename')
                pid = request.values.get('pid')
                total = request.values.get('total')
                page = request.values.get('page')
                pages = (int(page) - 1) * int(total)
                if use == "1" and gamename and pid:
                    games, gamesall = condb(
                        'SELECT `imagecover`.id,`imagecover`.imagename,`imagecover`.cover,`imagecover`.imageformat,`imagecover`.ginfo_id FROM `imageproject` INNER JOIN `imagecover` ON `imageproject`.iid = `imagecover`.id INNER JOIN `project` ON `imageproject`.pid=`project`.id INNER JOIN `gamelist` ON `imagecover`.ginfo_id = `gamelist`.id WHERE project.`id`="{}" AND ginfo_id IS NOT NULL AND `gamelist`.title LIKE "%%{}%%" ORDER BY `imagecover`.id DESC LIMIT {},{};'.format(
                            pid, gamename, pages, total))
                    ta, tas = condb(
                        'SELECT `imagecover`.id,`imagecover`.cover,`imagecover`.ginfo_id FROM `imageproject` INNER JOIN `imagecover` ON `imageproject`.iid = `imagecover`.id INNER JOIN `project` ON `imageproject`.pid=`project`.id INNER JOIN `gamelist` ON `imagecover`.ginfo_id = `gamelist`.id WHERE project.`id`="{}" AND ginfo_id IS NOT NULL AND `gamelist`.title LIKE "%%{}%%";'.format(
                            pid, gamename))
                elif use == "1" and pid:
                    games, gamesall = condb(
                        'SELECT `imagecover`.id,`imagecover`.imagename,`imagecover`.cover,`imagecover`.imageformat,`imagecover`.ginfo_id FROM `imageproject` INNER JOIN `imagecover` ON `imageproject`.iid = `imagecover`.id INNER JOIN `gamelist` ON `imagecover`.ginfo_id = `gamelist`.id WHERE ginfo_id IS NOT NULL AND  imageproject.`pid`="{}" ORDER BY `imagecover`.id DESC LIMIT {},{};'.format(
                            pid, pages, total))
                    ta, tas = condb(
                        'SELECT COUNT(`imagecover`.id) AS total FROM `imageproject` INNER JOIN `imagecover` ON `imageproject`.iid = `imagecover`.id INNER JOIN `gamelist` ON `imagecover`.ginfo_id = `gamelist`.id WHERE ginfo_id IS NOT NULL AND  imageproject.`pid`="{}";'.format(
                            pid))
                elif use == "1" and gamename:
                    games, gamesall = condb(
                        'SELECT `imagecover`.id,`imagecover`.imagename,`imagecover`.cover,`imagecover`.imageformat,`imagecover`.ginfo_id FROM `imagecover` INNER JOIN `gamelist` ON `imagecover`.ginfo_id = `gamelist`.id WHERE ginfo_id IS NOT NULL AND `gamelist`.title LIKE "%%{}%%" ORDER BY `imagecover`.id DESC LIMIT {},{};'.format(
                            gamename, pages, total))
                    ta, tas = condb(
                        'SELECT COUNT(`imagecover`.id) AS total FROM `imagecover` INNER JOIN `gamelist` ON `imagecover`.ginfo_id = `gamelist`.id WHERE ginfo_id IS NOT NULL AND `gamelist`.title LIKE "%%{}%%";'.format(
                            gamename))
                elif use == "1":
                    games, gamesall = condb(
                        'SELECT * FROM `imagecover` WHERE ginfo_id IS NOT NULL ORDER BY id DESC LIMIT {},{};'.format(pages, total))
                    ta, tas = condb('SELECT COUNT(id) AS total FROM `imagecover` WHERE ginfo_id IS NOT NULL;')
                elif use == "0":
                    games, gamesall = condb(
                        'SELECT * FROM `imagecover` WHERE ginfo_id IS NULL ORDER BY id DESC LIMIT {},{};'.format(pages, total))
                    ta, tas = condb('SELECT COUNT(id) AS total FROM `imagecover` WHERE ginfo_id IS NULL;')
                elif gamename:
                    games, gamesall = condb(
                        'SELECT `imagecover`.id,`imagecover`.imagename,`imagecover`.cover,`imagecover`.imageformat,`imagecover`.ginfo_id FROM `imagecover` INNER JOIN `gamelist` ON `imagecover`.ginfo_id = `gamelist`.id WHERE `gamelist`.title LIKE "%%{}%%" ORDER BY `imagecover`.id DESC LIMIT {},{};'.format(
                            gamename, pages, total))
                    ta, tas = condb(
                        'SELECT COUNT(`imagecover`.id) AS total FROM `imagecover` INNER JOIN `gamelist` ON `imagecover`.ginfo_id = `gamelist`.id WHERE `gamelist`.title LIKE "%%{}%%";'.format(
                            gamename))
                elif pid:
                    games, gamesall = condb(
                        'SELECT `imagecover`.id,`imagecover`.imagename,`imagecover`.cover,`imagecover`.imageformat,`imagecover`.ginfo_id,`project`.id,`project`.name FROM `imageproject` INNER JOIN `imagecover` ON `imageproject`.iid = `imagecover`.id INNER JOIN `project` ON `imageproject`.pid=`project`.id WHERE `project`.id="{}" ORDER BY `imagecover`.id DESC LIMIT {},{};'.format(
                            pid, pages, total))
                    ta, tas = condb(
                        'SELECT COUNT(`imagecover`.id) AS total FROM `imageproject` INNER JOIN `imagecover` ON `imageproject`.iid = `imagecover`.id INNER JOIN `project` ON `imageproject`.pid=`project`.id WHERE `project`.id="{}";'.format(
                            pid))
                else:
                    ta, tas = condb('SELECT COUNT(id) AS total FROM imagecover;')
                    games, gamesall = condb(
                        'SELECT * FROM (SELECT * FROM `imagecover` WHERE ginfo_id IS NOT NULL) AS tem UNION ALL (SELECT * FROM `imagecover` WHERE ginfo_id IS NULL) ORDER BY id DESC LIMIT {},{};'.format(
                            pages, total))
                return jsonify(gamesall, ta)
        return render_template('loadpage.html')
    return redirect('/')


@blue_loadpage.route('/add', methods=['POST', 'GET'])
def loadpageadd():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('loadpage'):
        if request.method == 'POST':
            htmlpage = request.values.get('htmlpage') + '.html'
            pid = request.values.get('pid')
            tempid = request.values.get('tempid')
            coverlist = request.values.get('coverlist')
            htmlpageone, htmlpageall = condb(
                'SELECT * FROM `loadpage` WHERE htmlpage="{}" AND pid="{}";'.format(htmlpage, pid))
            if htmlpageone:
                return jsonify(False)
            condb(
                'INSERT INTO `loadpage` (username,htmlpage,coverlist,ctime,pid,tempid) VALUES ("%s","%s","%s",NOW(),"%s","%s");' % (
                    username, htmlpage, coverlist, pid, tempid))
            return jsonify('success')
    return redirect('/')


@blue_loadpage.route('/update', methods=['POST', 'GET'])
def loadpageupdate():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('loadpage'):
        if request.method == 'POST':
            lid = request.values.get('lid')
            tempid = request.values.get('tempid')
            coverlist = request.values.get('coverlist')
            condb(
                'UPDATE `loadpage` SET `username`="{}",`coverlist`="{}",`ctime` = NOW(),`tempid`="{}" WHERE `id`="{}";'.format(
                    username, coverlist, tempid, lid))
            return jsonify('success')
    return redirect('/')


@blue_loadpage.route('/image/add', methods=['POST', 'GET'])
def imageadd():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('loadpage'):
        if request.method == 'POST':
            imageformat = request.values.get('imageformat')
            cover = request.values.get('cover')
            if cover:
                condb(
                    'INSERT INTO `imagecover` (cover,imageformat,username,ctime) VALUES ("%s","%s","%s",NOW());' % (cover, imageformat, username))
                return jsonify('success')
            else:
                pool = ThreadPoolExecutor(1)
                f = request.files['file']
                pool.submit(imagetobase, f, username, 'images/base64')
                return jsonify('success')
    return redirect('/')


@blue_loadpage.route('/image/update', methods=['POST', 'GET'])
def imageupdate():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('loadpage'):
        if request.method == 'POST':
            cover = request.values.get('cover')
            imageid = request.values.get('id')
            imagename = request.values.get('resources')
            projectlist = request.values.get('project')
            ginfo_id = request.values.get('ginfoid')
            gameinfoid, gameinfoidall = condb(
                'SELECT ginfo_id,old_id FROM `imagecover` WHERE id="{}";'.format(imageid))
            if gameinfoid.get('ginfo_id') or gameinfoid.get('old_id'):
                condb(
                    'UPDATE `imagecover` SET `username`="{}",`ctime` = NOW(),`ginfo_id`="{}" WHERE `id`="{}";'.format(
                        username, ginfo_id, imageid))
            else:
                condb(
                    'UPDATE `imagecover` SET `imagename`="{}",`username`="{}",`ctime` = NOW(),`ginfo_id`="{}" WHERE `id`="{}";'.format(
                        imagename, username, ginfo_id, imageid))
            if cover:
                condb(
                    'UPDATE `imagecover` SET `cover`="{}",`username`="{}",`ctime` = NOW() WHERE `id`="{}";'.format(
                        cover, username, imageid))
            if projectlist:
                condb('DELETE FROM `imageproject` WHERE iid="{}";'.format(imageid))
                for i in projectlist.split(','):
                    condb('INSERT INTO `imageproject` (iid,pid) VALUES ("%s","%s");' % (imageid, i))
            else:
                condb('DELETE FROM `imageproject` WHERE iid="{}";'.format(imageid))
            return jsonify('success')
    return redirect('/')
