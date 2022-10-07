from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from function.report import reportsasset

blue_assets = Blueprint('blue_assets', __name__, url_prefix='/assets')


@blue_assets.route('/', methods=['POST', 'GET'])
def assets():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        if request.method == 'POST':
            if request.values.get('select') == 'select':
                assetslist, assetsall = condb(
                    'SELECT assets.`id`,`type`,category,brand,model,sn,`count`,location,assets.`usage`,assets.ctime,assets.utime,assets.`code`,assets.`remark`,pid,chinesename FROM `assets` LEFT JOIN `person` ON assets.`pid` = person.`id` ORDER BY id DESC;')
                return jsonify(assetsall)
            elif request.values.get('select') == 'person':
                pers, persall = condb('SELECT id,chinesename FROM person;')
                return jsonify(persall)
        return render_template('assets.html')
    return redirect('/')


@blue_assets.route('/update', methods=['POST', 'GET'])
def assetsupdate():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "assets";')
            pid = request.values.get('pid')
            type = request.values.get('type')
            category = request.values.get('category')
            brand = request.values.get('brand')
            model = request.values.get('model')
            sn = request.values.get('sn')
            counts = request.values.get('count')
            location = request.values.get('location')
            usage = request.values.get('usage')
            ctime = request.values.get('ctime')
            utime = request.values.get('utime')
            code = request.values.get('code')
            remark = request.values.get('remark')
            if request.values.get('id'):
                sid = request.values.get('id')
                if pid:
                    condb(
                        'UPDATE `assets` SET `pid` = "{}",`type` = "{}",`category` = "{}",`brand` = "{}",`model` = "{}",`sn` = "{}",`count`="{}",`location`="{}",`usage`="{}",`ctime` = "{}",`utime` = "{}",`code`="{}",`remark`="{}" WHERE `id`="{}";'.format(
                            pid, type, category, brand, model, sn, counts, location, usage, ctime, utime, code, remark,
                            sid))
                else:
                    condb(
                        'UPDATE `assets` SET `pid` = NULL,`type` = "{}",`category` = "{}",`brand` = "{}",`model` = "{}",`sn` = "{}",`count`="{}",`location`="{}",`usage`="{}",`ctime` = "{}",`utime` = "{}",`code`="{}",`remark`="{}" WHERE `id`="{}";'.format(
                            type, category, brand, model, sn, counts, location, usage, ctime, utime, code, remark,
                            sid))
            else:
                if pid:
                    condb(
                        'INSERT INTO `assets` (`pid`,`type`,category,brand,model,sn,`count`,location,`usage`,ctime,utime,code,remark) VALUES ("%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s");' % (
                            pid, type, category, brand, model, sn, counts, location, usage, ctime, utime, code,
                            remark))
                else:
                    condb(
                        'INSERT INTO `assets` (`pid`,`type`,category,brand,model,sn,`count`,location,`usage`,ctime,utime,code,remark) VALUES (NULL,"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s");' % (
                            type, category, brand, model, sn, counts, location, usage, ctime, utime, code,
                            remark))
            condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "assets";')
            return jsonify('success')
    return redirect('/')


@blue_assets.route('/book', methods=['POST', 'GET'])
def assetsbook():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        if request.method == 'POST':
            book, books = condb(
                'SELECT book.`id`,`name`,`type`,author,press,sn,`number`,unit,source,mender,buytime,cost,book.`utime`,gtime,book.`status`,book.`remark`,pid,chinesename FROM `book` LEFT JOIN `person` ON book.`pid` = person.`id` ORDER BY id DESC;')
            return jsonify(books)
    return redirect('/')


@blue_assets.route('/book/update', methods=['POST', 'GET'])
def assetsbookupdate():
    author = session.get('author')
    if author.get('manager') or author.get('assets'):
        if request.method == 'POST':
            condb('UPDATE `splock` SET `lock` = 1 WHERE `function` = "assets";')
            bid = request.values.get('bid')
            name = request.values.get('name')
            type = request.values.get('type')
            author = request.values.get('author')
            press = request.values.get('press')
            sn = request.values.get('sn')
            number = request.values.get('number')
            unit = request.values.get('unit')
            source = request.values.get('source')
            mender = request.values.get('mender')
            buytime = request.values.get('buytime')
            cost = request.values.get('cost')
            utime = request.values.get('utime')
            gtime = request.values.get('gtime')
            status = request.values.get('status')
            remark = request.values.get('remark')
            pid = request.values.get('pid')
            if bid:
                if utime and pid and gtime:
                    condb(
                        'UPDATE `book` SET `name`="{}",`type`="{}",author="{}",press="{}",sn="{}",`number`="{}",unit="{}",source="{}",mender="{}",buytime="{}",cost="{}",utime="{}",gtime="{}",status="{}",remark="{}",pid="{}" WHERE id="{}";'.format(
                            name, type, author, press, sn, number, unit, source, mender, buytime, cost,
                            utime, gtime, status, remark, pid, bid))
                elif utime and pid:
                    condb(
                        'UPDATE `book` SET `name`="{}",`type`="{}",author="{}",press="{}",sn="{}",`number`="{}",unit="{}",source="{}",mender="{}",buytime="{}",cost="{}",utime="{}",gtime=NULL,status="{}",remark="{}",pid="{}" WHERE id="{}";'.format(
                            name, type, author, press, sn, number, unit, source, mender, buytime, cost,
                            utime, status, remark, pid, bid))
                else:
                    condb(
                        'UPDATE `book` SET `name`="{}",`type`="{}",author="{}",press="{}",sn="{}",`number`="{}",unit="{}",source="{}",mender="{}",buytime="{}",cost="{}",utime=NULL,gtime=NULL,status="{}",remark="{}",pid=NULL WHERE id="{}";'.format(
                            name, type, author, press, sn, number, unit, source, mender, buytime, cost, status, remark, bid))
                condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "assets";')
                return jsonify('success')
            condb(
                'INSERT INTO `book` (`name`,`type`,author,press,sn,`number`,unit,source,mender,buytime,cost,utime,gtime,status,remark,pid) VALUES ("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}",NULL,NULL,"{}","{}",NULL);'.format(
                    name, type, author, press, sn, number, unit, source, mender, buytime, cost, status,
                    remark))
            condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "assets";')
            return jsonify('success')
    return redirect('/')
