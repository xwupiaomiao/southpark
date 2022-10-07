from .conndb import condb


def serverip(project):
    resip, resipall = condb(
        'SELECT `ip` FROM `project` INNER JOIN `server` ON project.`sid` = server.`id` WHERE `name`="{}";'.format(
            project))
    return resip.get('ip')


def serveripaddr(hostname):
    resip, resipall = condb('SELECT `ip` FROM `server` WHERE `sname`="{}";'.format(hostname))
    return resip.get('ip')


def serveripid(sid):
    resip, resipall = condb('SELECT `ip`,`sname` FROM `server` WHERE `id`="{}";'.format(sid))
    return resip.get('ip'),resip.get('sname')


def getserverip(projectid):
    resip, resipall = condb(
        'SELECT `ip`,`name` FROM `project` INNER JOIN `server` ON project.`sid` = server.`id` WHERE project.`id`="{}";'.format(
            projectid))
    return resip.get('ip'), resip.get('name')
