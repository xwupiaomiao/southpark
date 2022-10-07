from flask import Blueprint
from flask import request, session, jsonify, redirect, render_template
from function.conndb import condb
from function.auth import AD
from function.report import reportsasset

blue_person = Blueprint('blue_person', __name__, url_prefix='/person')


@blue_person.route('/', methods=['POST', 'GET'])
def person():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        if request.method == 'POST':
            if request.values.get('select') == 'select':
                pers, persall = condb(
                    'SELECT * FROM `person` LEFT JOIN `job` ON person.`jid`=job.`id` ORDER BY person.`id` DESC;')
                return jsonify(persall)
            elif request.values.get('select') == 'job':
                joblist, jobslist = condb('SELECT * FROM `job`;')
                return jsonify(jobslist)
        return render_template('person.html')
    return redirect('/')


@blue_person.route('/update', methods=['POST', 'GET'])
def personupdate():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        if request.method == 'POST':
            id = request.values.get('id')
            mobile = request.values.get('mobile')
            birthday = request.values.get('birthday')
            mail = request.values.get('mail')
            utime = request.values.get('utime')
            device = request.values.get('device')
            status = request.values.get('status')
            personremark = request.values.get('personremark')
            jid = request.values.get('jid')
            remark = request.values.get('remark')
            if utime:
                perlist, perall = condb(
                    'SELECT job.`name`,chinesename,person.`utime` FROM `person` INNER JOIN `job` ON person.`jid`=job.`id` WHERE person.id="{}";'.format(
                        id))
                dn = 'CN=%s,OU=south,DC=southpark,DC=com' % (perlist.get('chinesename'))
                AD().clock_unclock(dn, False)
                reportsasset(perlist.get('chinesename'), perlist.get('name'), utime)
                condb(
                    'UPDATE person SET utime="{}",status="{}" WHERE id="{}";'.format(
                        utime, status, id))
                return jsonify('success')
            condb(
                'UPDATE person p INNER JOIN job j SET p.mobile="{}",p.birthday="{}",p.mail="{}",p.utime=NULL,p.device="{}",p.status="{}",p.personremark="{}",p.jid="{}",j.`remark`="{}" WHERE p.id="{}" AND j.id="{}";'.format(
                    mobile, birthday, mail, device, status, personremark, jid, remark, id, jid))
            return jsonify('success')
    return redirect('/')


@blue_person.route('/add', methods=['POST', 'GET'])
def personadd():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "person";')
            first = request.values.get('first')
            second = request.values.get('second')
            sex = request.values.get('sex')
            birthday = request.values.get('birthday')
            mobile = request.values.get('mobile')
            mail = request.values.get('mail')
            ctime = request.values.get('ctime')
            device = request.values.get('device')
            personremark = request.values.get('personremark')
            jid = request.values.get('jid')
            remark = request.values.get('remark')
            perlist, perall = condb('SELECT `name` FROM `job` WHERE id="{}";'.format(jid))
            dn = 'CN=%s,OU=south,DC=southpark,DC=com' % (first + second)
            attr = {
                'cn': first + second,
                'displayName': '%s, %s' % (first, second),
                'distinguishedName': dn,
                'givenName': second,
                'name': first + second,
                'objectCategory': 'CN=Person,CN=Schema,CN=Configuration,DC=southpark,DC=com',
                'userPrincipalName': '%s@southpark.com' % (mail),
                'sAMAccountName': mail,
                'sn': first,
                'telephoneNumber': mobile,
                'mail': '%s@papayamobile.com' % (mail),
                'description': [perlist.get('name')]
            }
            try:
                AD().create_obj(dn, 'user', attr)
                condb(
                    'INSERT INTO `person` (username,chinesename,sex,birthday,mobile,mail,ctime,device,`status`,personremark,jid) VALUES ("%s","%s","%s","%s","%s","%s","%s","%s",1,"%s","%s");' % (
                        mail, first + second, sex, birthday, mobile, mail + '@papayamobile.cn', ctime, device,
                        personremark, jid))
                condb('UPDATE `job` SET `remark` = "{}" WHERE `id` = "{}";'.format(remark, jid))
                if device == "1":
                    reportsasset(first + second, perlist.get('name'), ctime, status=True,
                                 device='台式机')
                if device == "2":
                    reportsasset(first + second, perlist.get('name'), ctime, status=True,
                                 device='笔记本')
                if device == "3":
                    reportsasset(first + second, perlist.get('name'), ctime, status=True,
                                 device='自备电脑')
                tag = 'success'
            except Exception as e:
                print(e)
                tag = False
            finally:
                condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "person";')
            return jsonify(tag)
    return redirect('/')


@blue_person.route('/delete', methods=['POST', 'GET'])
def persondelete():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        if request.method == 'POST':
            id = request.values.get('id')
            perlist, perall = condb(
                'SELECT chinesename FROM `person` WHERE id="{}";'.format(id))
            dn = 'CN=%s,OU=south,DC=southpark,DC=com' % (perlist.get('chinesename'))
            AD().del_obj(dn)
            condb('DELETE FROM person WHERE id="{}";'.format(id))
            return jsonify('success')
    return redirect('/')


@blue_person.route('/layout', methods=['POST', 'GET'])
def personlayout():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        layout, layoutall = condb(
            'SELECT layout.`id`,desk,location,chinesename,job.`name`,job.`remark`,person.`status`,person.`ctime`,person.`utime`,layout.`pid` FROM `layout` LEFT JOIN `person` ON layout.`pid` = person.`id` LEFT JOIN job ON person.`jid` = job.`id`;')
        return jsonify(layoutall)
    return redirect('/')


@blue_person.route('/layout/update', methods=['POST', 'GET'])
def personlayoutupdate():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        if request.method == 'POST':
            if request.values.get('select') == 'person':
                pers, persall = condb('SELECT id,chinesename FROM person;')
                return jsonify(persall)
            else:
                id = request.values.get('id')
                pid = request.values.get('pid')
                if pid:
                    condb('UPDATE `layout` SET `pid` = "{}" WHERE `id`="{}";'.format(pid, id))
                else:
                    condb('UPDATE `layout` SET `pid` = NULL WHERE `id`="{}";'.format(id))
                return jsonify('success')
    return redirect('/')
