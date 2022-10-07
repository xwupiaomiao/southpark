from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from concurrent.futures import ThreadPoolExecutor
from function.conndb import condb
from function.report import reportdns
from function.cdnngx import updatedns, deletedns, adddnsadmin
import json, time, os

blue_addomain = Blueprint('blue_addomain', __name__, url_prefix='/admin/domain')


@blue_addomain.route('/', methods=['POST', 'GET'])
def addomain():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            setable = request.values.get('table')
            projectname = request.values.get('project')
            if setable == 'zoneinfo':
                sitin, sitinall = condb(
                    ' SELECT zoneinfo.`id`,`zone`,zone_id,account FROM zoneinfo INNER JOIN `cdnaccount` ON zoneinfo.`cdnaccount_id` = cdnaccount.`id`;')
            elif setable == 'domainzone':
                sitin, sitinall = condb(
                    'SELECT domainzone.`id`,`site`,`chname`,`zone`,`account` FROM `domainzone` INNER JOIN siteinfo ON siteinfo.`id`= domainzone.`sid` INNER JOIN `zoneinfo` ON zoneinfo.`id` = domainzone.`zid` INNER JOIN `cdnaccount` ON zoneinfo.`cdnaccount_id` = cdnaccount.`id` ORDER BY id DESC;')
            elif setable == 'domain':
                sitin, sitinall = condb(
                    'SELECT domain.`id`,`url`,`oldip`,`newip`,`proxy`,`zone` FROM `domain` INNER JOIN zoneinfo ON zoneinfo_id = zoneinfo.`id` ORDER BY domain.`id` DESC;')
            elif setable == 'addbulk':
                sitin, sitinall = condb(
                    'SELECT zoneinfo.`id`,`zone` FROM domain INNER JOIN zoneinfo ON zoneinfo_id = zoneinfo.`id` GROUP BY zoneinfo.`id`;')
            elif setable == 'zoneinfo':
                sitin, sitinall = condb('SELECT `id`,`zone` FROM zoneinfo;')
            elif projectname:
                with open('/root/scripts/conf/{}'.format(projectname), 'r', encoding='utf-8') as f:
                    return jsonify('{}'.format(f.read()))
            else:
                sitin, sitinall = condb(' SELECT * FROM {};'.format(setable))
            return jsonify(sitinall)
        return render_template('admin/domain.html')
    return redirect('/')


@blue_addomain.route('/add', methods=['POST', 'GET'])
def addomainadd():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            table = request.values.get('table')
            if table == 'domainzone':
                sid = request.values.get('sid')
                zid = request.values.get('zid')
                domainzonecheck, domainzonecheckall = condb(
                    ' SELECT `id` FROM domainzone WHERE `sid` = "{}" AND `zid` = "{}";'.format(sid, zid))
                if domainzonecheck:
                    return jsonify(False)
                else:
                    condb('INSERT INTO `%s` (sid,zid) VALUES ("%s","%s");' % (table, sid, zid))
                    return jsonify('success')
            if table == 'cdnaccount':
                account = request.values.get('account')
                account_id = request.values.get('account_id')
                api_key = request.values.get('api_key')
                condb('INSERT INTO `%s` (account,account_id,api_key) VALUES ("%s","%s","%s");' % (
                    table, account, account_id, api_key))
                return jsonify('success')
            if table == 'zoneinfo':
                zone = request.values.get('zone')
                zone_id = request.values.get('zone_id')
                cdnaccount_id = request.values.get('cdnaccount_id')
                nginxconf = request.values.get('nginx')
                try:
                    with open('/root/scripts/conf/{}'.format(zone.split('.')[0]), 'w', encoding='utf-8') as f:
                        f.write(str(nginxconf))
                except Exception as e:
                    print(e)
                    return jsonify(False)
                else:
                    condb('INSERT INTO `%s` (`zone`,zone_id,cdnaccount_id) VALUES ("%s","%s","%s");' % (
                        table, zone, zone_id, cdnaccount_id))
                return jsonify('success')
            if table == 'siteinfo':
                site = request.values.get('site')
                chname = request.values.get('chname')
                condb('INSERT INTO `%s` (`site`,chname) VALUES ("%s","%s");' % (
                    table, site, chname))
                '' if os.path.exists("/root/3nm-web/site/conf/{}".format(site)) else os.mkdir(
                    "/root/3nm-web/site/conf/{}".format(site))
                return jsonify('success')
    return redirect('/')


@blue_addomain.route('/del', methods=['POST', 'GET'])
def addomaindel():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            did = request.values.get('did')
            condb('DELETE FROM domainzone WHERE id="{}";'.format(did))
            return jsonify('success')
    return redirect('/')


@blue_addomain.route('/adddns', methods=['POST', 'GET'])
def adddns():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            username = session.get('user_info')
            hostname = request.values.get('hostname')
            zoneinfoid = request.values.get('zoneinfoid')
            ipaddress = request.values.get('ipaddress')
            proxy = request.values.get('proxy')
            cdnmassge, cdnmassgeall = condb(
                'SELECT `zone`,`zone_id`,`account`,`api_key` FROM zoneinfo INNER JOIN cdnaccount ON cdnaccount_id = cdnaccount.`id` WHERE zoneinfo.`id`="{}";'.format(
                    zoneinfoid))
            domain_name = '{}.{}'.format(hostname.strip(), cdnmassge.get('zone')) if hostname else cdnmassge.get('zone')
            urlcheck, urlcheckall = condb('SELECT `id` FROM domain WHERE `url`="{}";'.format(domain_name))
            if urlcheck:
                return jsonify('域名已存在')
            else:
                resadd = adddnsadmin(username, cdnmassge.get('zone_id'), cdnmassge.get('account'),
                                     cdnmassge.get('api_key'),
                                     ipaddress, hostname, domain_name, zoneinfoid, json.loads(proxy))
                if resadd:
                    return jsonify('success')
                else:
                    return jsonify('域名添加失败')
    return redirect('/')


@blue_addomain.route('/editdns', methods=['POST', 'GET'])
def editdns():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            username = session.get('user_info')
            zoneinfoid = request.values.get('zoneinfoid')
            ipaddress = request.values.get('ipaddress')
            domainid = request.values.get('domainid')
            proxy = request.values.get('proxy')
            if domainid:
                cdnmassge, cdnmassgeall = condb(
                    'SELECT `url`,`urlid`,`zone_id`,`account`,`api_key` FROM domain INNER JOIN zoneinfo ON zoneinfo_id = zoneinfo.`id` INNER JOIN cdnaccount ON cdnaccount_id = cdnaccount.`id` WHERE domain.`id`="{}";'.format(
                        domainid))
                resold, resnew = updatedns(cdnmassge.get('url'), cdnmassge.get('zone_id'), cdnmassge.get('urlid'),
                                           cdnmassge.get('account'), cdnmassge.get('api_key'), ipaddress,
                                           json.loads(proxy))
                reportdns(username, "开启" if json.loads(proxy) else "关闭", "https://{}".format(cdnmassge.get('url')),
                          time.strftime("%Y-%m-%d"" ""%H:%M:%S"), "修改成功", resnew.json().get('result').get('content'),
                          resold.json().get('result').get('content'))
            else:
                urllist = []
                pool = ThreadPoolExecutor(2)
                cdnmassge, cdnmassgeall = condb(
                    'SELECT `url`,`urlid`,`zone_id`,`account`,`api_key`,`oldip` FROM domain INNER JOIN zoneinfo ON zoneinfo_id = zoneinfo.`id` INNER JOIN cdnaccount ON cdnaccount_id = cdnaccount.`id` WHERE `zoneinfo_id`="{}" AND `nginx`=1;'.format(
                        zoneinfoid))
                for i in cdnmassgeall:
                    urllist.append(i.get('url'))
                    pool.submit(updatedns, i.get('url'), i.get('zone_id'), i.get('urlid'),
                                i.get('account'), i.get('api_key'), ipaddress, json.loads(proxy))
            return jsonify('success')
    return redirect('/')


@blue_addomain.route('/deldns', methods=['POST', 'GET'])
def deldns():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            username = session.get('user_info')
            domainid = request.values.get('domainid')
            cdnmassge, cdnmassgeall = condb(
                'SELECT `url`,`urlid`,`newip`,`oldip`,`zone_id`,`account`,`proxy`,`api_key` FROM domain INNER JOIN zoneinfo ON zoneinfo_id = zoneinfo.`id` INNER JOIN cdnaccount ON cdnaccount_id = cdnaccount.`id` WHERE domain.`id`="{}";'.format(
                    domainid))
            deletedns(cdnmassge.get('zone_id'), cdnmassge.get('urlid'), cdnmassge.get('account'),
                      cdnmassge.get('api_key'))
            condb('DELETE FROM `domain` WHERE id="{}";'.format(domainid))
            reportdns(username, "开启" if json.loads(cdnmassge.get('proxy')) else "关闭",
                      "https://{}".format(cdnmassge.get('url')),
                      time.strftime("%Y-%m-%d"" ""%H:%M:%S"), "删除成功", cdnmassge.get('newip'), cdnmassge.get('oldip'))
            return jsonify('success')
    return redirect('/')
