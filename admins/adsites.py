from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from function.sshsftp import comupload
from function.getip import getserverip
import os

blue_adsites = Blueprint('blue_adsites', __name__, url_prefix='/admin/sites')

'''项目管理'''


@blue_adsites.route('/', methods=['POST', 'GET'])
def adsites():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            if request.values.get('select') == 'server':
                serverl, serverall = condb(' SELECT * FROM server;')
                return jsonify(serverall)
            if request.values.get('select') == 'zoneinfo':
                zonea, zoneall = condb(' SELECT id,`zone` FROM zoneinfo;')
                return jsonify(zoneall)
            if request.values.get('select') == 'template':
                module = request.values.get('module')  # module 有两种取值 pc 和 pcmobile
                with open(f'/root/3nm-web/site/template/{module}', 'r', encoding='utf-8') as f:
                    return jsonify('{}'.format(f.read()))
            if request.values.get('select') == 'nginx':
                projectname = request.values.get('project')
                with open('/root/scripts/conf/{}'.format(projectname), 'r', encoding='utf-8') as f:
                    return jsonify('{}'.format(f.read()))
            proj, projall = condb(
                ' SELECT project.`id`,`name`,`url`,`status`,`zone`,`sname`,`forbiden` FROM project INNER JOIN zoneinfo ON project.`zoneinfo_id` = zoneinfo.`id` INNER JOIN server ON project.`sid` = server.`id`;')
            return jsonify(projall)
        return render_template('admin/sites.html')
    return redirect('/')


@blue_adsites.route('/add', methods=['POST', 'GET'])
def adsitesadd():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            giturl = request.values.get('giturl')
            filename = request.values.get('filename')
            newfilename = request.values.get('newfilename')
            zoneinfo_id = request.values.get('zoneinfo_id')
            sid = request.values.get('sid')
            if filename == newfilename:
                res = os.system(
                    'cd /root/3nm-web && git clone {} && cd {} && yarn'.format(giturl, filename))
            else:
                res = os.system(
                    'cd /root/3nm-web && git clone {} && mv {} {} && cd {} && yarn'.format(giturl, filename,
                                                                                           newfilename, newfilename))
            if res == 0:
                fileid, fileidall = condb('SELECT id FROM project WHERE `name` = "{}";'.format(newfilename))
                if zoneinfo_id:
                    condb(
                        'INSERT INTO `project` (`name`,status,zoneinfo_id,sid,forbiden) VALUES ("%s",1,"%s","%s",1);' % (
                            newfilename, zoneinfo_id, sid))
                    condb('INSERT INTO `engineer` (ctime,status,pid) VALUES (NOW(),NULL,"%s");' % (fileid.get('id')))
                    condb('INSERT INTO `advert` (ctime,lock,status,pid) VALUES (NOW(),NULL,NULL,"%s");' % (
                        fileid.get('id')))
                else:
                    condb('INSERT INTO `project` (`name`,status,sid,forbiden) VALUES ("%s",1,"%s",1);' % (
                    newfilename, sid))
                    condb('INSERT INTO `engineer` (ctime,status,pid) VALUES (NOW(),NULL,"%s");' % (fileid.get('id')))
                    condb('INSERT INTO `advert` (ctime,lock,status,pid) VALUES (NOW(),NULL,NULL,"%s");' % (
                        fileid.get('id')))
                return jsonify('success')
            else:
                return jsonify(False)
    return redirect('/')


@blue_adsites.route('/edit', methods=['POST', 'GET'])
def adsitesedit():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            pid = request.values.get('pid')
            filename = request.values.get('filename')
            url = request.values.get('url')
            # nginx配置修改
            addr = url.split('//')[-1]
            nginxconf = request.values.get('nginx_conf')
            zoneinfo_id = request.values.get('zoneinfo_id')
            sid = request.values.get('sid')
            proje, projeall = condb('SELECT `name` FROM project WHERE id="{}"'.format(pid))
            if filename != proje.get('name'):
                res = os.system('cd /root/3nm-web && mv {} {}'.format(proje.get('name'), filename))
                if res != 0:
                    return jsonify(False)
            elif zoneinfo_id:
                condb('UPDATE `project` SET `name`="{}",`url`="{}",`zoneinfo_id`="{}",`sid`="{}" WHERE id="{}";'.format(
                    filename, url, zoneinfo_id, sid, pid))
                if nginxconf:
                    site_one, site_all = condb('SELECT site FROM siteinfo;')
                    for i in site_all:
                        new_nginxconf = nginxconf % {'project': filename, 'addr': addr, 'site': i.get('site')}
                        with open(f'/root/3nm-web/site/conf/{i.get("site")}/{filename}_{i.get("site")}', 'w',
                                  encoding='utf-8') as f:
                            f.write(str(new_nginxconf))
                    os.system('ssh root@172.17.0.3 "service nginx restart"')
            else:
                condb('UPDATE `project` SET `name`="{}",`url`="{}",`sid`="{}" WHERE id="{}";'.format(filename, url, sid,
                                                                                                     pid))
            return jsonify('success')
    return redirect('/')


@blue_adsites.route('/del', methods=['POST', 'GET'])
def adsitesdel():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            pid = request.values.get('pid')
            condb('DELETE FROM project WHERE id="{}";'.format(pid))
            return jsonify('success')
    return redirect('/')


@blue_adsites.route('/editnginx', methods=['POST', 'GET'])
def editnginx():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            pid = request.values.get('pid')
            nginxconf = request.values.get('nginxconf')
            sites, sitesall = condb(
                'SELECT site FROM domainzone INNER JOIN siteinfo ON sid=siteinfo.`id` WHERE zid = (SELECT zoneinfo_id FROM project WHERE id="{}");'.format(
                    pid))
            serveripaddr, projectname = getserverip(pid)
            sshclient = comupload(serveripaddr)
            for i in sitesall:
                servername = ""
                urlone, urlall = condb(
                    'SELECT site,`domain`.url FROM `domain` INNER JOIN project ON domain.`zoneinfo_id` = project.`zoneinfo_id` WHERE project.`id`="{}" AND site = "{}";'.format(
                        pid, i.get('site')))
                for u in urlall:
                    servername += u.get('url') + ' '
                if urlone:
                    new_nginxconf = nginxconf % {'project': projectname, 'servername': servername.strip(),
                                                 'site': i.get('site')}
                    with open(f'/root/scripts/nginx_conf/{projectname}_{i.get("site")}', 'w',
                              encoding='utf-8') as f:
                        f.write(str(new_nginxconf))
                    sshclient.upload(f'/root/scripts/nginx_conf/{projectname}_{i.get("site")}',
                                     f'/etc/nginx/sites-enabled/{projectname}_{i.get("site")}')
                    sshclient.comand(
                        f'if [[ ! -d /var/log/nginx/{projectname}/{i.get("site")} ]]; then mkdir -p /var/log/nginx/{projectname}/{i.get("site")};fi')
            sshclient.upload('/root/scripts/conf/nginx.conf', '/etc/nginx/nginx.conf')
            sshclient.comand(
                'if [[ ! -d /sitebackup/{project}/conf ]]; then mkdir -p /sitebackup/{project}/conf;fi && cp /etc/nginx/sites-enabled/{project}_* /sitebackup/{project}/conf'.format(
                    project=projectname))
            sshclient.comand('systemctl reload nginx.service')
            os.system('rm -fr /root/scripts/nginx_conf/{}_*'.format(projectname))
            sshclient.sshclose()
            return jsonify('success')
    return redirect('/')


@blue_adsites.route('/forbiden', methods=['POST', 'GET'])
def forbidenproject():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            forbiden = request.values.get('forbiden')
            pid = request.values.get('pid')
            condb('UPDATE `project` SET `forbiden`="{}" WHERE id="{}";'.format(forbiden, pid))
            return jsonify('success')
    return redirect('/')
