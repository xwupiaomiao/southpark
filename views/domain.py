from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from concurrent.futures import ThreadPoolExecutor
from function.cdnngx import nginxconf, cdn

blue_domain = Blueprint('blue_domain', __name__, url_prefix='/domain')


@blue_domain.route('/', methods=['POST', 'GET'])
def domain():
    author = session.get('author')
    if author.get('manager') or author.get('domain'):
        if request.method == 'POST':
            table = request.values.get('table')
            domainame = request.values.get('domainame')
            if table == 'project':
                if len(session.get('project')) == 1:
                    res, resall = condb('SELECT zoneinfo.`id`,`name`,`zone` FROM project INNER JOIN `zoneinfo` ON zoneinfo.`id` = project.`zoneinfo_id` WHERE project.`name` = "{}";'.format(session.get('project')[0]))
                    return jsonify(resall)
                else:
                    res, resall = condb('SELECT zoneinfo.`id`,`name`,`zone` FROM project INNER JOIN `zoneinfo` ON zoneinfo.`id` = project.`zoneinfo_id` WHERE project.`name` IN {};'.format(tuple(session.get('project'))))
                    return jsonify(resall)
            elif table == 'domainzone':
                res, resall = condb(
                    'SELECT `site`,`chname`,`zone` FROM `domainzone` INNER JOIN siteinfo ON siteinfo.`id`= domainzone.`sid` INNER JOIN `zoneinfo` ON zoneinfo.`id` = domainzone.`zid` WHERE zone="{}";'.format(
                        domainame))
                return jsonify(resall)
            elif table == 'domaininfo':
                if request.values.get('select') == 'select':
                    search = request.values.get('search')
                    site = request.values.get('site')
                    page = request.values.get('page')
                    total = request.values.get('total')
                    pages = (int(page) - 1) * int(total)
                    if site and search:
                        res, resall = condb(
                            'SELECT * FROM `domain` WHERE `site`="{}" AND `url` LIKE "%%{}%%" OR `site`="{}" AND `username` LIKE "%%{}%%" ORDER BY id DESC LIMIT {},{};'.format(
                                site, search, site, search, pages, total))
                        counts, countsall = condb(
                            'SELECT COUNT(id) as total FROM `domain` WHERE `site`="{}" AND `url` LIKE "%%{}%%" OR `site`="{}" AND `username` LIKE "%%{}%%" ORDER BY id DESC;'.format(
                                site, search, site, search))
                        return jsonify(resall, counts)
                    elif site:
                        res, resall = condb(
                            'SELECT * FROM `domain` WHERE `site`="{}" ORDER BY id DESC LIMIT {},{};'.format(
                                site, pages, total))
                        counts, countsall = condb(
                            'SELECT COUNT(id) as total FROM `domain` WHERE `site`="{}";'.format(site))
                        return jsonify(resall, counts)
                    elif search:
                        res, resall = condb(
                            'SELECT * FROM `domain` WHERE `url` LIKE "%%{}%%" OR `username` LIKE "%%{}%%" ORDER BY id DESC LIMIT {},{};'.format(
                                search, search, pages, total))
                        counts, countsall = condb(
                            'SELECT COUNT(id) as total FROM `domain` WHERE `url` LIKE "%%{}%%" OR `username` LIKE "%%{}%%" ORDER BY id DESC;'.format(
                                search, search))
                        return jsonify(resall, counts)
                    else:
                        res, resall = condb(
                            'SELECT * FROM `domain` ORDER BY id DESC LIMIT {},{};'.format(pages, total))
                        counts, countsall = condb('SELECT COUNT(id) as total FROM `domain`;')
                        return jsonify(resall, counts)
        sites, sites_all = condb('SELECT `site`,`chname` FROM `siteinfo`;')
        return render_template('domain.html', sites_all=sites_all)
    return redirect('/')


@blue_domain.route('/add', methods=['POST', 'GET'])
def domainadd():
    username = session.get('user_info')
    author = session.get('author')
    if author.get('manager') or author.get('domain'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "domain"')
            domainame = request.values.get('domainame')
            zoneinfo_id = request.values.get('zoneinfoid')
            project = request.values.get('project')
            site = request.values.get('site')
            addr = request.values.get('addr')
            if addr:
                urlcheck, urlall = condb(
                    'SELECT `url` FROM `domain` WHERE `url`="{}";'.format(addr + '.' + domainame))
            else:
                urlcheck, urlall = condb(
                    'SELECT `url` FROM `domain` WHERE `url`="{}";'.format(domainame))
            if urlcheck:
                condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "domain"')
                return jsonify(False)
            else:
                pool = ThreadPoolExecutor(1)
                pool.submit(nginxconf, username, project, site, domainame, addr, zoneinfo_id).add_done_callback(cdn)
                return jsonify('success')
    return redirect('/')
