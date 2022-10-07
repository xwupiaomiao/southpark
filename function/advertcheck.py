import os
import json
from PIL import Image
from .sshsftp import comupload
from .conndb import condb
import time
from .report import reports


def check_content(rootdir):
    content_error = []
    for root, dirs, files in os.walk(rootdir):
        # print("====================")
        # print(f'root {root}')
        # print(f'dir:{dirs}')
        # print(f'files:{files}')
        # print("====================")
        for file in files:
            origin_name = file
            path_list = origin_name.split('.')
            pre_path = path_list[0]
            last_path = path_list[-1]
            if last_path in ['jpg', 'jpeg', 'png', 'JPEG', 'JPG', 'PNG']:
                img = Image.open(os.path.join(root, file))
                size = img.size
                if size[0] == size[1] and size[0] < 1800:
                    pre_path += '_square'
                elif round(size[0]/size[1], 3) == 1.911 and size[0] < 1800:
                    pre_path += '_long'
                else:
                    print(f'wrong image ratio: {os.path.join(root, file)}')
                    content_error.append(f'wrong image ratio: {os.path.join(root, file)}')
                img.close()
                new_name = pre_path + '.' + last_path
                if new_name != origin_name:
                    os.rename(os.path.join(root, file),
                              os.path.join(root, new_name))
            if last_path == 'json':
                with open(os.path.join(root, file), 'rb') as f:
                    try:
                        data = json.load(f)
                    except:
                        content_error.append(f'json文件有问题:{root}')
                        continue
                    for headline in data['Headlines']:
                        if len(headline) > 30:
                            print(f'headline over size: {root} {headline}')
                            content_error.append(
                                f'headline over size: {root} {headline}')
                        if ',' in headline:
                            print(
                                f'headline unacceptable spacing: {root} {headline}')
                            content_error.append(
                                f'headline unacceptable spacing: {root} {headline}')
                    if len(set(data['Headlines'])) != len(data['Headlines']):
                        print(f'duplicated headlines: {root}')
                        content_error.append(f'duplicated headlines: {root}')
                    if len(data["Long headline"]) > 90:
                        print(
                            f'long headline over size: {root} {data["Long headline"]}')
                        content_error.append(
                            f'long headline over size: {root} {data["Long headline"]}')
                    for des in data['Descriptions']:
                        if len(des) > 90:
                            print(f'description over size: {root} {des}')
                            content_error.append(
                                f'description over size: {root} {des}')
                        if '?' in des and '? ' not in des:
                            print(
                                f'decription unacceptable spacing: {root} {des}')
                            content_error.append(
                                f'decription unacceptable spacing: {root} {des}')
    return content_error


def check_number(rootdir):
    number_error = []
    for root, dirs, files in os.walk(rootdir):
        if 'LK' in os.path.basename(root) or 'PP' in os.path.basename(root):
            dir_num = len(dirs)
            if dir_num > 6:
                number_error.append(f'dir numbers > 6 {root}')
        if len(files) > 0 and files[0].split('.')[-1] in ['jpg', 'jpeg', 'png', 'JPEG', 'JPG', 'PNG', 'json']:
            square_num = 0
            long_num = 0
            json_num = 0
            for file in files:
                origin_name = file
                path_list = origin_name.split('.')
                pre_path = path_list[0]
                last_path = path_list[-1]
                if 'long' in pre_path:
                    long_num += 1
                if 'square' in pre_path:
                    square_num += 1
                if 'json' in last_path:
                    json_num += 1
                    os.rename(os.path.join(root, file),
                              os.path.join(root, 'template.json'))
            if long_num == 0 or square_num == 0 or json_num == 0:
                number_error.append(files)
    return number_error


def check_ads_sucai(rootdir):
    content_errors = check_content(rootdir)
    if len(content_errors) > 0:
        print(content_errors)
        return content_errors
    num_errors = check_number(rootdir)
    if len(num_errors) > 0:
        print(num_errors)
        return num_errors
    return 0


def uploadadvert(username, project):
    condb('UPDATE advert a INNER JOIN project p ON a.`pid` = p.`id` SET a.username="{}",a.ctime=NOW(),a.status=1,a.lock=1 WHERE p.name="{}";'.format(username, project))
    condb('INSERT INTO `advertlog` (project,username,ctime,status) VALUES ("%s","%s",NOW(),1);' % (project, username))
    reports("用户：{}".format(username), "项目：{}，开始上传广告".format(project), time.strftime("%Y-%m-%d"" ""%H:%M:%S"))
    sshadv = comupload('104.238.135.197')
    os.system('cd advert/file && tar -zcf {}.tar.gz {}'.format(project, project))
    sshadv.upload('advert/file/{}.tar.gz'.format(project), '/root/cms_be/adimg/{}.tar.gz'.format(project))
    resall, reserr, ecode = sshadv.exec_com('cd /root/cms_be/adimg && tar xf {}.tar.gz && cd /root/cms_be && /root/.cache/pypoetry/virtualenvs/cms-be-rpEgFfBe-py3.8/bin/python fastapi_tools/add_ad_to_certain_adgroups_noseed.py {} {}'.format(project, username, project))
    if ecode == 0:
        condb('UPDATE `advertlog` SET `status` = 2,`ctime` = NOW(),`msg`="{}" WHERE `project`="{}" AND `username`="{}" AND `status`=1;'.format(resall, project, username))
        condb('UPDATE advert a INNER JOIN project p ON a.`pid` = p.`id` SET a.username="{}",a.ctime=NOW(),a.status=2,a.lock=0 WHERE p.name="{}";'.format(username, project))
        sshadv.exec_com('cd /root/cms_be/adimg && rm -fr {}.tar.gz'.format(project))
        sshadv.sshclose()
        reports("用户：{}".format(username), "项目：{}，广告上传完成".format(project), time.strftime("%Y-%m-%d"" ""%H:%M:%S"))
    else:
        condb('UPDATE `advertlog` SET `status` = 3,`ctime` = NOW(),`msg`="{}" WHERE `project`="{}" AND `username`="{}" AND `status`=1;'.format('脚本运行错误，请联系陈静', project, username))
        condb('UPDATE advert a INNER JOIN project p ON a.`pid` = p.`id` SET a.username="{}",a.ctime=NOW(),a.status=3,a.lock=0 WHERE p.name="{}";'.format(username, project))
        sshadv.exec_com('cd /root/cms_be/adimg && rm -fr {}.tar.gz'.format(project))
        sshadv.sshclose()
        reports("用户：{}".format(username), "项目：{}，广告上传失败".format(project), time.strftime("%Y-%m-%d"" ""%H:%M:%S"))
    os.remove('advert/file/{}.tar.gz'.format(project))
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "advert"')
