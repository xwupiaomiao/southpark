from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from concurrent.futures import ThreadPoolExecutor
from function.upvideo import upgamesvideo, savevideo
from function.unzip import saveimage
from function.sshsftp import comupload
from function.getip import serveripaddr
import os

blue_gamelist = Blueprint('blue_gamelist', __name__, url_prefix='/gamelist')


@blue_gamelist.route('/', methods=['POST', 'GET'])
def games():
    author = session.get('author')
    if author.get('manager') or author.get('video'):
        if request.method == 'POST':
            if request.values.get('select') == 'select':
                page = request.values.get('page')
                total = request.values.get('total')
                pages = (int(page) - 1) * int(total)
                modules = request.values.get('modules')
                resources = request.values.get('resources')
                if modules and resources:
                    games, gamesall = condb(
                        'SELECT *  FROM `gamelist` WHERE modules = "{}" AND resources LIKE "%%{}%%" ORDER BY id DESC LIMIT {},{};'.format(
                            modules, resources, pages, total))
                    counts, countsall = condb(
                        'SELECT COUNT(id) as total FROM `gamelist` WHERE modules = "{}" AND resources LIKE "%%{}%%" ORDER BY id DESC;'.format(
                            modules, resources))
                    return jsonify(gamesall, counts)
                elif modules:
                    games, gamesall = condb(
                        'SELECT *  FROM `gamelist` WHERE modules = "{}" ORDER BY id DESC LIMIT {},{};'.format(
                            modules, pages, total))
                    counts, countsall = condb(
                        'SELECT COUNT(id) as total FROM `gamelist` WHERE modules = "{}" ORDER BY id DESC;'.format(
                            modules))
                    return jsonify(gamesall, counts)
                elif resources:
                    games, gamesall = condb(
                        'SELECT *  FROM `gamelist` WHERE resources LIKE "%%{}%%" ORDER BY id DESC LIMIT {},{};'.format(
                            resources, pages, total))
                    counts, countsall = condb(
                        'SELECT COUNT(id) as total FROM `gamelist` WHERE resources LIKE "%%{}%%" ORDER BY id DESC;'.format(
                            resources))
                    return jsonify(gamesall, counts)
                else:
                    games, gamesall = condb(
                        'SELECT *  FROM `gamelist` ORDER BY id DESC LIMIT {},{};'.format(pages, total))
                    counts, countsall = condb('SELECT COUNT(id) as total FROM `gamelist` ORDER BY id DESC;')
                    return jsonify(gamesall, counts)
            elif request.values.get('select') == 'modules':
                games, gamesall = condb('SELECT `id`,`name` FROM `modules`;')
                return jsonify(gamesall)
            elif request.values.get('select') == 'resources':
                modulesid = request.values.get('id')
                games, gamesall = condb(
                    'SELECT resources.`id`,resources.`name` FROM `resources` INNER JOIN `modules` ON resources.`mid`= modules.`id` WHERE modules.`id`="{}";'.format(
                        modulesid))
                return jsonify(gamesall)
        return render_template('gamelist.html')
    return redirect('/')


@blue_gamelist.route('/update', methods=['POST', 'GET'])
def gamesupdate():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('video'):
        if request.method == 'POST':
            gamelistid = request.values.get('id')
            title = request.values.get('title')
            description = request.values.get('description')
            edit_review = request.values.get('edit_review')
            script = request.values.get('script')
            filename = request.values.get('filename')
            imagename = request.values.get('imagename')
            if title:
                condb(
                    'UPDATE `gamelist` SET `username`="{}",`title`="{}",`ctime` = NOW() WHERE `id`="{}";'.format(
                        username, title, gamelistid))
            if description:
                condb(
                    'UPDATE `gamelist` SET `username`="{}",`description`="{}",`ctime` = NOW() WHERE `id`="{}";'.format(
                        username, description, gamelistid))
            if edit_review:
                condb(
                    'UPDATE `gamelist` SET `username`="{}",`edit_review`="{}",`ctime` = NOW() WHERE `id`="{}";'.format(
                        username, edit_review, gamelistid))
            if filename:
                condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "gamelist"')
                zipname = gamelistid + '.mp4'
                gamevideourl = 'http://video.sp.com/gamevideo/' + zipname
                pool = ThreadPoolExecutor(1)
                pool.submit(upgamesvideo, script, filename, zipname, username, gamelistid, gamevideourl)
            if imagename:
                condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "gamelist"')
                f = request.files['file']
                saveimage(f, '/root/3nm-web/site/images', imagename, username)
                if 'video' in imagename:
                    condb(
                        'UPDATE `gamelist` SET `username`="{}",`video`="{}",`ctime` = NOW() WHERE `id`="{}";'.format(
                            username, 'http://image.sp.com/' + imagename, gamelistid))
                elif 'game1' in imagename:
                    condb(
                        'UPDATE `gamelist` SET `username`="{}",`game1`="{}",`ctime` = NOW() WHERE `id`="{}";'.format(
                            username, 'http://image.sp.com/' + imagename, gamelistid))
                elif 'game2' in imagename:
                    condb(
                        'UPDATE `gamelist` SET `username`="{}",`game2`="{}",`ctime` = NOW() WHERE `id`="{}";'.format(
                            username, 'http://image.sp.com/' + imagename, gamelistid))
                elif 'game3' in imagename:
                    condb(
                        'UPDATE `gamelist` SET `username`="{}",`game3`="{}",`ctime` = NOW() WHERE `id`="{}";'.format(
                            username, 'http://image.sp.com/' + imagename, gamelistid))
            if not gamelistid:
                pool = ThreadPoolExecutor(1)
                f = request.files['file']
                pool.submit(savevideo, f, '../video/upload')
            return jsonify('success')
    return redirect('/')


@blue_gamelist.route('/add', methods=['POST', 'GET'])
def gamesadd():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('video'):
        if request.method == 'POST':
            modules = request.values.get('modules')
            resources = request.values.get('resources')
            testurl = 'http://game.sp.com/{}/?name={}'.format(modules, resources)
            moduleresources, moduleresourcesall = condb(
                'SELECT `id` FROM `gamelist` WHERE `modules` = "{}" AND `resources` = "{}";'.format(modules,
                                                                                                    resources))
            if moduleresources:
                return jsonify(False)
            else:
                condb(
                    'INSERT INTO `gamelist` (username,test_url,ctime,modules,resources) VALUES ("%s","%s",NOW(),"%s","%s");' % (
                        username, testurl, modules, resources))
                return jsonify('success')
    return redirect('/')


@blue_gamelist.route('/del', methods=['POST', 'GET'])
def gamesdel():
    author = session.get('author')
    if author.get('manager') or author.get('video'):
        if request.method == 'POST':
            gamelistid = request.values.get('id')
            gamelistdel, gamelistdelall = condb(
                'SELECT video,game1,game2,game3,gamevideourl FROM gamelist WHERE id="{}"'.format(gamelistid))
            imagevideo = gamelistdel.get('video').split('/')[-1]
            gamevideo = gamelistdel.get('gamevideourl').split('/')[-1]
            imagegame1 = gamelistdel.get('game1').split('/')[-1]
            imagegame2 = gamelistdel.get('game2').split('/')[-1]
            imagegame3 = gamelistdel.get('game3').split('/')[-1]
            os.system('cd /root/3nm-web/site/images && rm -fr {} {} {} {}'.format(imagevideo, imagegame1, imagegame2,
                                                                                  imagegame3))
            os.system('cd /var/www/video/gamevideo && rm -fr {}'.format(gamevideo))
            imagecmd = comupload(serveripaddr('image'))
            imagecmd.comand(
                'cd /var/www/html/images && rm -fr {} {} {} {}'.format(imagevideo, imagegame1, imagegame2, imagegame3))
            imagecmd.sshclose()
            gamevideohost = comupload(serveripaddr('gamevideo'))
            gamevideohost.comand('cd /var/www/html/gamevideo && rm -fr {}'.format(gamevideo))
            gamevideohost.sshclose()
            condb('DELETE FROM gamelist WHERE id="{}";'.format(gamelistid))
            return jsonify('success')
    return redirect('/')
