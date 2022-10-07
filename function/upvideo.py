import time
from .report import reports
from .getip import serveripaddr
from .conndb import condb
from .sshsftp import comupload
import requests
import json, os


def savevideo(f, savepath):
    basepath = os.path.dirname(__file__)
    upload_path = os.path.join(basepath, savepath, f.filename)
    f.save(upload_path)


def upanvideo(script, filename, videoinfo, zipname, username):
    """
    上传动画视频
    :return:
    """
    testurl = 'http://video.sp.com/animationvideo/' + zipname
    title = videoinfo.get('title')
    youtube_id = videoinfo.get('youtube_id')
    category = videoinfo.get('category')
    tag = videoinfo.get('tag')
    cat_id = videoinfo.get('cat_id')
    description = videoinfo.get('description')
    condb(
        'INSERT INTO `video` (title,youtube_id,category,tag,username,testurl,requesturl,ctime,status,description,cat_id) VALUES ("%s","%s","%s","%s","%s","%s","%s",NOW(),1,"%s","%s");' % (
            title, youtube_id, category, tag, username, testurl,'https://video.superbaby.tv/{}'.format(zipname), description, cat_id))
    res = os.system(script)
    if res == 0:
        condb('UPDATE `video` SET `status` = 2 WHERE `youtube_id`="{}";'.format(youtube_id))
        reports("用户：{}".format(username), "视频：{}，开始上传".format(zipname), time.strftime("%Y-%m-%d"" ""%H:%M:%S"))
        serverip = serveripaddr('animationvideo')
        video = comupload(serverip)
        video.upload('/root/southpark/video/animationvideo/' + zipname, '/var/www/html/mp4video' + '/' + zipname)
        video.comand(
            "if [[ ! -d /var/www/html/m3u8video/{filename} ]];then mkdir /var/www/html/m3u8video/{filename} && ffmpeg -i /var/www/html/mp4video/{filename}.mp4 -f segment -segment_time 10 -segment_format mpegts -segment_list /var/www/html/m3u8video/{filename}/{filename}.m3u8 -c copy -bsf:v h264_mp4toannexb -map 0 /var/www/html/m3u8video/{filename}/{filename}%03d.ts;fi".format(
                filename=youtube_id))
        video.sshclose()
        reports("用户：{}".format(username), "视频：{}，上传完成".format(zipname), time.strftime("%Y-%m-%d"" ""%H:%M:%S"),
                url='https://video.superbaby.tv/{}'.format(zipname))
        os.remove('/root/southpark/video/upload/' + filename.replace(" ", "_"))
        condb('UPDATE `video` SET `status` = 3 WHERE `youtube_id`="{}";'.format(youtube_id))
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "video";')


def uptoyvideo(script, filename, videoinfo, zipname, username):
    testurl = 'http://video.sp.com/toyvideo/' + zipname
    title = videoinfo.get('title')
    youtube_id = videoinfo.get('youtube_id')
    category = videoinfo.get('category')
    tag = videoinfo.get('tag')
    cat_id = videoinfo.get('cat_id')
    description = videoinfo.get('description')
    condb(
        'INSERT INTO `video` (title,youtube_id,category,tag,username,testurl,requesturl,ctime,status,description,cat_id) VALUES ("%s","%s","%s","%s","%s","%s","%s",NOW(),1,"%s","%s");' % (
            title, youtube_id, category, tag, username, testurl,'https://video.playtoys.tv/{}'.format(zipname), description, cat_id))
    res = os.system(script)
    if res == 0:
        condb('UPDATE `video` SET `status` = 2 WHERE `youtube_id`="{}";'.format(youtube_id))
        reports("用户：{}".format(username), "视频：{}，开始上传".format(zipname), time.strftime("%Y-%m-%d"" ""%H:%M:%S"))
        serverip = serveripaddr('toyvideo')
        video = comupload(serverip)
        video.upload('/root/southpark/video/toyvideo/' + zipname, '/var/www/html/toyvideo/' + zipname)
        video.sshclose()
        condb('UPDATE `video` SET `status` = 3 WHERE `youtube_id`="{}";'.format(youtube_id))
        os.remove('/root/southpark/video/upload/' + filename.replace(" ", "_"))
        reports("用户：{}".format(username), "视频：{}，上传完成".format(zipname), time.strftime("%Y-%m-%d"" ""%H:%M:%S"),
                url='https://video.toyplay.tv/{}'.format(zipname))
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "video";')


def upgamesvideo(script, filename, zipname, username, ginfoid, gamevideourl):
    res = os.system(script)
    if res == 0:
        reports("用户：{}".format(username), "视频：{}，开始上传".format(zipname), time.strftime("%Y-%m-%d"" ""%H:%M:%S"))
        condb('UPDATE `gamelist` SET `status`=2 WHERE `id`="{}";'.format(ginfoid))
        serverip = serveripaddr('gamevideo')
        video = comupload(serverip)
        video.upload('/root/southpark/video/gamevideo/' + zipname, '/var/www/html/gamevideo/' + zipname)
        video.sshclose()
        reports("用户：{}".format(username), "视频：{}，上传完成".format(zipname), time.strftime("%Y-%m-%d"" ""%H:%M:%S"),
                url='https://gamevideo.toyplay.tv/{}'.format(zipname))
        os.remove('/root/southpark/video/upload/' + filename.replace(" ", "_"))
        condb(
            'UPDATE `gamelist` SET `username`="{}",`gamevideourl`="{}",`ctime` = NOW(),`status`=3 WHERE `id`="{}";'.format(
                username, gamevideourl, ginfoid))
    else:
        condb('UPDATE `gamelist` SET `status`=4 WHERE `id`="{}";'.format(ginfoid))
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "gamelist"')


def upvideotocdn(requesturl, title, zoneinfo_id):
    res, resall = condb(
        'SELECT account,account_id,api_key FROM zoneinfo INNER JOIN cdnaccount ON zoneinfo.`cdnaccount_id` = cdnaccount.`id` WHERE zoneinfo.id="{}"'.format(
            zoneinfo_id))
    headers = {
        'X-Auth-Email': res.get('account'),
        'X-Auth-Key': res.get('api_key'),
    }
    videodata = {'url': requesturl, 'meta': {'name': title}}
    rescdn = requests.post(
        url="https://api.cloudflare.com/client/v4/accounts/{}/stream/copy".format(res.get('account_id')),
        headers=headers,
        data=json.dumps(videodata))
    return rescdn
