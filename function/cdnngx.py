#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import requests
import json
import os
from .sshsftp import comupload
from .conndb import condb
import time
from .report import reports, reportdns
from .getip import serverip

cdnapiurl = "https://api.cloudflare.com/client/v4/zones"
site_path = '/var/www/html'
nginx_conf_path = '/etc/nginx/sites-enabled'


def cdn(resultdata):
    site, domainname, url, addr, username, cdnaddr, nstat, errmag = resultdata.result()
    res, resall = condb(
        'SELECT domain.`id`,`zone`,`zone_id`,`account`,`api_key` FROM `domain` INNER JOIN `zoneinfo` ON zoneinfo_id = zoneinfo.`id` INNER JOIN `cdnaccount` ON cdnaccount.`id` = zoneinfo.`cdnaccount_id` WHERE `zone` = "{}"  AND domain.`url` = "{}";'.format(
            domainname, url))
    headers = {
        'X-Auth-Email': res.get('account'),
        'X-Auth-Key': res.get('api_key'),
        'Content-Type': 'application/json',
        'Connection': 'close'
    }
    if url == domainname:
        reqdata = {"type": "A", "name": domainname, "content": cdnaddr, "ttl": 3600, "priority": 10, "proxied": True}
    else:
        reqdata = {"type": "A", "name": addr, "content": cdnaddr, "ttl": 3600, "priority": 10, "proxied": True}
    if nstat:
        res1 = requests.post(url="{}/{}/dns_records".format(cdnapiurl, res.get('zone_id')), headers=headers,
                             data=json.dumps(reqdata))
        if res1.json().get('success'):
            message = errmag.replace('\n', '<br />') + '新增域名：{}&nbsp;&nbsp;&nbsp;&nbsp;'.format(
                res1.json().get('result').get('name')) + '绑定IP：{}'.format(res1.json().get('result').get('content'))
            condb(
                "UPDATE `domain` SET `message` = '{}',urlid='{}',oldip='{}',newip='{}',`status` = 3,`ctime` = NOW() WHERE `id`='{}';".format(
                    message, res1.json().get('result').get('id'), res1.json().get('result').get('content'),
                    res1.json().get('result').get('content'),
                    res.get('id')))
            reports("用户：{}".format(username), "域名：{}，添加成功".format(url), time.strftime("%Y-%m-%d"" ""%H:%M:%S"),
                    "https://{}".format(url))
        else:
            message = errmag.replace('\n', '<br />') + json.dumps(res1.json().get('errors')) + '<br />' + json.dumps(
                res1.json().get('messages'))
            condb(
                "UPDATE `domain` SET `message` = '{}',`status` = 2,`ctime` = NOW() WHERE `id`='{}';".format(
                    message, res.get('id')))
    else:
        message = errmag.replace('\n', '<br />')
        condb(
            "UPDATE `domain` SET `message` = '{}',`status` = 1,`ctime` = NOW() WHERE `id`='{}';".format(
                message, res.get('id')))
        reports("用户：{}".format(username), "域名：{}，添加失败，请联系管理员".format("https://{}".format(url)),
                time.strftime("%Y-%m-%d"" ""%H:%M:%S"))
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "domain"')


def nginxconf(username, project, site, domainname, addr, zoneinfo_id):
    res, resall = condb(
        'SELECT `url` FROM `domain` WHERE `site`="{}" AND `zoneinfo_id`="{}" AND `nginx`=1;'.format(site, zoneinfo_id))
    if addr:
        url = addr + '.' + domainname
        condb(
            'INSERT INTO `domain` (`site`,`url`,`addr`,`username`,`ctime`,`status`,`zoneinfo_id`) VALUES ("%s","%s","%s","%s",NOW(),4,"%s");' % (
                site, url, addr, username, zoneinfo_id))
    else:
        url = domainname
        condb(
            'INSERT INTO `domain` (`site`,`url`,`username`,`ctime`,`status`,`zoneinfo_id`) VALUES ("%s","%s","%s",NOW(),4,"%s");' % (
                site, url, username, zoneinfo_id))
    reports("用户：{}".format(username), "域名：{}，开始添加".format(url), time.strftime("%Y-%m-%d"" ""%H:%M:%S"),
            "https://{}".format(url))
    servername = ""
    for i in resall:
        servername += i.get('url') + ' '
    servername = servername + url
    cdnaddr = serverip(project)
    with open('/root/scripts/conf/{}'.format(project), 'r', encoding='utf-8') as f:
        rel = f.read()
    with open('/root/scripts/nginx_conf/{}_{}'.format(project, site), 'w', encoding='utf-8') as f:
        f.write(rel % ({'project': project, 'site': site, 'servername': servername}))
    exec = comupload(cdnaddr)
    exec.upload('/root/scripts/nginx_conf/{}_{}'.format(project, site),
                '/etc/nginx/sites-enabled/{}_{}'.format(project, site))
    remasg, errmasg = exec.comand(
        'if [[ ! -d /var/log/nginx/{project}/{site} ]]; then mkdir -p /var/log/nginx/{project}/{site};fi && /usr/sbin/nginx -t'.format(
            project=project, site=site))
    if 'successful' in errmasg and '[warn]' not in errmasg:
        exec.comand('systemctl reload nginx.service')
        exec.sshclose()
        os.system('rm -fr /root/scripts/nginx_conf/{}_{}'.format(project, site))
        return site, domainname, url, addr, username, cdnaddr, True, errmasg
    else:
        exec.sshclose()
        os.system('rm -fr /root/scripts/nginx_conf/{}_{}'.format(project, site))
        return site, domainname, url, addr, username, cdnaddr, False, errmasg


def adddnsadmin(username, zone_id, account, api_key, ipaddress, hostname, domainname, zoneinfo_id, proxy):
    requrl = "{}/{}/dns_records".format(cdnapiurl, zone_id)
    headers = {
        'X-Auth-Email': account,
        'X-Auth-Key': api_key,
        'Content-Type': 'application/json',
        'Connection': 'close'
    }
    reqdata = {"type": "A", "name": domainname, "content": ipaddress, "ttl": 1, "priority": 10, "proxied": proxy}
    resreq = requests.post(url=requrl, headers=headers, data=json.dumps(reqdata))
    if resreq.json().get('success'):
        message = '新增域名：{}&nbsp;&nbsp;&nbsp;&nbsp;'.format(resreq.json().get('result').get('name')) + '绑定IP：{}'.format(
            resreq.json().get('result').get('content'))
        if proxy:
            condb(
                'INSERT INTO `domain` (`url`,`addr`,`urlid`,`oldip`,`newip`,`username`,`message`,`zoneinfo_id`,`ctime`,`status`,`nginx`) VALUES ("%s","%s","%s","%s","%s","%s","%s","%s",NOW(),3,2);' % (
                    domainname, hostname, resreq.json().get('result').get('id'),
                    resreq.json().get('result').get('content'),
                    resreq.json().get('result').get('content'), username, message, zoneinfo_id))
        else:
            condb(
                'INSERT INTO `domain` (`url`,`addr`,`urlid`,`oldip`,`newip`,`username`,`message`,`zoneinfo_id`,`ctime`,`proxy`,`status`,`nginx`) VALUES ("%s","%s","%s","%s","%s","%s","%s","%s",NOW(),"false",3,2);' % (
                    domainname, hostname, resreq.json().get('result').get('id'),
                    resreq.json().get('result').get('content'),
                    resreq.json().get('result').get('content'), username, message, zoneinfo_id))
        reportdns(username, "开启" if proxy else "关闭", "https://{}".format(domainname),
                  time.strftime("%Y-%m-%d"" ""%H:%M:%S"), "添加成功", ipaddress)
        return True
    else:
        reportdns(username, "开启" if proxy else "关闭", "https://{}".format(domainname),
                  time.strftime("%Y-%m-%d"" ""%H:%M:%S"), "添加失败", ipaddress)
        return False


def updatedns(url, zone_id, urlid, account, api_key, ipaddress, proxy):
    requrl = "{}/{}/dns_records/{}".format(cdnapiurl, zone_id, urlid)
    headers = {
        'X-Auth-Email': account,
        'X-Auth-Key': api_key,
        'Content-Type': 'application/json',
        'Connection': 'close'
    }
    reqdata = {"type": "A", "name": url, "content": ipaddress, "ttl": 1, "priority": 10,
               "proxied": proxy}
    resold = requests.get(url=requrl, headers=headers)
    resnew = requests.put(url=requrl, headers=headers, data=json.dumps(reqdata))
    if proxy:
        condb('UPDATE `domain` SET `oldip` = "{}",`newip` = "{}",`proxy` = "true" WHERE `url` = "{}";'.format(
            resold.json().get('result').get('content'),
            resnew.json().get('result').get('content'), url))
    else:
        condb('UPDATE `domain` SET `oldip` = "{}",`newip` = "{}",`proxy` = "false" WHERE `url` = "{}";'.format(
            resold.json().get('result').get('content'),
            resnew.json().get('result').get('content'), url))
    return resold, resnew


def deletedns(zone_id, urlid, account, api_key):
    requrl = "{}/{}/dns_records/{}".format(cdnapiurl, zone_id, urlid)
    headers = {
        'X-Auth-Email': account,
        'X-Auth-Key': api_key,
        'Content-Type': 'application/json',
        'Connection': 'close'
    }
    resresponse = requests.delete(url=requrl, headers=headers)
    return resresponse.json()


def clearcdncache(zone_id, account, api_key):
    requrl = "{}/{}/purge_cache".format(cdnapiurl, zone_id)
    headers = {
        'X-Auth-Email': account,
        'X-Auth-Key': api_key,
        'Content-Type': 'application/json',
        'Connection': 'close'
    }
    reqdata = {"purge_everything": True}
    resrequest = requests.post(url=requrl, headers=headers, data=json.dumps(reqdata))
    if resrequest.json().get('success'):
        return True, None
    else:
        return False, resrequest.json().get('errors')
