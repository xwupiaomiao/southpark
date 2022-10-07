import os
import json
import time
from function.conndb import condb
from function.sshsftp import comupload
from function.report import reports
from function.getip import serverip, serveripaddr
from function.cdnngx import clearcdncache
import subprocess


class UploadError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def create(project):
    # res = os.system("cd /root/3nm-web/{proname} && /root/.local/bin/poetry run python main.py".format(proname=project))
    res = os.system("cd /root/3nm-web/{proname} && yarn build".format(proname=project))
    if res == 0:
        condb(
            'UPDATE `project` SET `status` = 1,`ctime` = NOW(),`lock`=NULL,`sendsize`=NULL,`percent`=NULL WHERE `name`="{}";'.format(
                project
            )
        )
    else:
        condb(
            'UPDATE `project` SET `status` = 4,`ctime` = NOW(),`lock`=NULL,`sendsize`=NULL,`percent`=NULL WHERE `name`="{}";'.format(
                project
            )
        )
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "sites";')


def up(project, username):
    res = os.system(
        'cd /root/3nm-web/site && mv {proname} {proname}_new && tar -zcf {proname}.tar.gz {proname}_new && mv {proname}_new {proname}'.format(
            proname=project
        )
    )
    if res == 0:
        ipaddress = serverip(project)
        ssh = comupload(ipaddress, project=project)
        ssh.upload(
            '/root/3nm-web/site/{}.tar.gz'.format(project),
            '/var/www/html/{}.tar.gz'.format(project),
        )
        ssh.comand(
            'cd /var/www/html && if [[ ! -d /sitebackup/%(proname)s ]]; then mkdir -p /sitebackup/%(proname)s;fi && if [[ -d %(proname)s ]]; then tar -zcf /sitebackup/%(proname)s/%(proname)s_$(date +%%F).tar.gz %(proname)s;fi && tar xf %(proname)s.tar.gz && rm -fr %(proname)s && mv %(proname)s_new %(proname)s && chown -R root.root %(proname)s && rm -fr %(proname)s.tar.gz && find /sitebackup -type f -name "%(proname)s_*.tar.gz" -mtime +1 -exec rm -rf {} \;'
            % {'proname': project}
        )
        ssh.sshclose()
        os.system('rm -fr /root/3nm-web/site/{}.tar.gz'.format(project))
        condb(
            'UPDATE `project` SET `status` = 2,`ctime` = NOW(),`lock`=NULL,`rolback`=1 WHERE `name`="{}";'.format(
                project
            )
        )
        condb(
            'INSERT INTO `uploadlog` (proname,username,ctime,stat) VALUES ("%s","%s",NOW(),1);'
            % (project, username)
        )
    prourl, prourlall = condb(
        'SELECT `zone`,`zone_id`,`account`,`api_key` FROM `project` INNER JOIN zoneinfo ON project.`zoneinfo_id` = zoneinfo.`id` INNER JOIN cdnaccount ON cdnaccount_id = cdnaccount.`id` WHERE `name`="{}";'.format(
            project
        )
    )
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "sites";')
    reports(
        "用户：{}".format(username),
        "站点：{}，上线完成".format(json.dumps(project)),
        time.strftime("%Y-%m-%d %H:%M:%S"),
        'https://www.{}'.format(prourl.get('zone')),
    )


def up_data(project: str):
    """通过git同步生成数据到构建服务器

    Args:
        project (str): 项目名
        username (str): 操作人
    """
    ts = time.ctime()
    res = subprocess.run(
        'cd /root/3nm-web/data && git add {proname} && git commit -m "{proname}_{ts}"'.format(
            proname=project, ts=ts
        ),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f'up_data.returncode: {res.returncode}')
    print(f'up_data.stdout: {res.stdout}')
    stdout = str(res.stdout, encoding="utf-8")
    if (
        res.returncode == 0
        or 'Your branch is ahead of' in stdout
        or 'nothing to commit' in stdout
        or 'Your branch is up to date with' in stdout
        or 'nothing added to commit' in stdout
    ):
        if res.returncode == 0 or 'Your branch is ahead of' in stdout:
            push_res = subprocess.run(
                'cd /root/3nm-web/data && git push',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print(f'push_res.returncode: {push_res.returncode}')
            print(f'push_res.stdout: {push_res.stdout}')
            print(f'push_res.stderr: {push_res.stderr}')
            if push_res.returncode != 0:
                raise UploadError('up_data push error')
        # if res.returncode == 0 or (res.returncode == 1 and ('nothing to commit' in str(res.stdout, encoding="utf-8")) or 'Your branch is up to date with' in str(res.stdout, encoding="utf-8") or 'nothing added to commit' in str(res.stdout, encoding="utf-8")):
        try:
            manage_ipaddress = serveripaddr('projectManage')
            ssh = comupload(manage_ipaddress)

            stdout_pull, stderr_pull, exit_code_pull = ssh.exec_com(
                f'cd /root/3nm-web/data && git pull'
            )
            ssh.sshclose()
            print(f'pull_data.returncode: {exit_code_pull}')
            print(f'pull_data.stdout: {stdout_pull}')
            print(f'pull_data.stderr_pull: {stderr_pull}')
            print('up data finished')
            return exit_code_pull
        except Exception as e:
            print(f'e:{e}')
            raise UploadError('up_data error exec_com')
    else:
        print('--------------up data err-----------')
        raise UploadError('--------------up_data error---------------')


def create_manage(project: str, branch: str = None):
    """在构建服务器上生成项目

    Args:
        project (str): 项目名
    """
    print('create_manage started')

    up_data(project)
    manage_ipaddress = serveripaddr('projectManage')
    ssh = comupload(manage_ipaddress)
    try:
        if branch and 'dev' in branch:
            stdout_manage, stderr_manage, exit_code_manage = ssh.exec_com(
                f"cd /root/3nm-web/{project}_dev && yarn build_online && rm -rf /root/3nm-web/dev/{project} && cp -R /root/3nm-web/{project}_dev/sites/{project} /root/3nm-web/dev/"
            )
        else:
            stdout_manage, stderr_manage, exit_code_manage = ssh.exec_com(
                f"cd /root/3nm-web/{project} && yarn build_online && rm -rf /root/3nm-web/site/{project} && cp -R /root/3nm-web/{project}/sites/{project} /root/3nm-web/site/"
            )
        ssh.sshclose()
        # print(f'stdout_manage: {stdout_manage}')
        # print(f'stderr_manage: {stderr_manage}')
        # print(f'exit_code_manage: {exit_code_manage}')
    except Exception as e:
        raise UploadError(f'create_manage error exec_com: {e}')
    if exit_code_manage == 0:
        print('create_manage finished')
        return exit_code_manage
    else:
        raise UploadError('create_manage error')


def create_local(project: str, branch: str = None):
    """在本地服务器上生成项目和json数据

    Args:
        project (str): 项目名称
        branch (str): 分支名称
    """
    res = os.system(f"cd /root/3nm-web/{project} && yarn build")
    create_manage(project, branch)
    if branch is None:
        if res == 0:
            condb(
                'UPDATE `project` SET `status` = 1,`ctime` = NOW(),`lock`=NULL,`sendsize`=NULL,`percent`=NULL WHERE `name`="{}";'.format(
                    project
                )
            )
        else:
            condb(
                'UPDATE `project` SET `status` = 4,`ctime` = NOW(),`lock`=NULL,`sendsize`=NULL,`percent`=NULL WHERE `name`="{}";'.format(
                    project
                )
            )
        condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "sites";')


def up_manage(project: str, username: str):
    """将构建服务器上的项目上传至项目服务器,并在项目服务器上做备份解压等操作

    Args:
        project (str): 项目名
        username (str): 操作人
    """
    print('up_manage started')

    ipaddress = serverip(project)

    manage_ipaddress = serveripaddr('projectManage')
    ssh_manage = comupload(manage_ipaddress)

    stdout_manage, stderr_manage, exit_code_manage = ssh_manage.exec_com(
        f"cd /root/3nm-web/site && mv {project} {project}_new && tar -zcf {project}.tar.gz {project}_new && mv {project}_new {project} && scp {project}.tar.gz root@{ipaddress}:/var/www/html/ && rm -fr /root/3nm-web/site/{project}.tar.gz"
    )
    ssh_manage.sshclose()
    print(f'up_manage_code: {exit_code_manage}')
    print(f'up_manage_stdout: {stdout_manage}')
    print(f'up_manage_err: {stderr_manage}')
    if exit_code_manage == 0:
        server_ssh = comupload(ipaddress)
        _, _, code = server_ssh.exec_com(
            'cd /var/www/html && if [[ ! -d /sitebackup/%(proname)s ]]; then mkdir -p /sitebackup/%(proname)s;fi && if [[ -d %(proname)s ]]; then tar -zcf /sitebackup/%(proname)s/%(proname)s_$(date +%%F).tar.gz %(proname)s;fi && tar xf %(proname)s.tar.gz && rm -fr %(proname)s && mv %(proname)s_new %(proname)s && chown -R root.root %(proname)s && rm -fr %(proname)s.tar.gz && find /sitebackup -type f -name "%(proname)s_*.tar.gz" -mtime +1 -exec rm -rf {} \;'
            % {'proname': project}
        )
        server_ssh.sshclose()
        condb(
            'UPDATE `project` SET `status` = 2,`ctime` = NOW(),`lock`=NULL,`rolback`=1 WHERE `name`="{}";'.format(
                project
            )
        )
        condb(
            'INSERT INTO `uploadlog` (proname,username,ctime,stat) VALUES ("%s","%s",NOW(),1);'
            % (project, username)
        )
    else:
        prourl, prourlall = condb(
            'SELECT `zone`,`zone_id`,`account`,`api_key` FROM `project` INNER JOIN zoneinfo ON project.`zoneinfo_id` = zoneinfo.`id` INNER JOIN cdnaccount ON cdnaccount_id = cdnaccount.`id` WHERE `name`="{}";'.format(
                project
            )
        )
        condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "sites";')
        reports(
            "用户：{}".format(username),
            "站点：{}，上线出错".format(json.dumps(project)),
            time.strftime("%Y-%m-%d %H:%M:%S"),
            'https://www.{}'.format(prourl.get('zone')),
        )
        print('up_manage finished')

        raise UploadError("up_manage error")
    prourl, prourlall = condb(
        'SELECT `zone`,`zone_id`,`account`,`api_key` FROM `project` INNER JOIN zoneinfo ON project.`zoneinfo_id` = zoneinfo.`id` INNER JOIN cdnaccount ON cdnaccount_id = cdnaccount.`id` WHERE `name`="{}";'.format(
            project
        )
    )
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "sites";')
    reports(
        "用户：{}".format(username),
        "站点：{}，上线完成".format(json.dumps(project)),
        time.strftime("%Y-%m-%d %H:%M:%S"),
        'https://www.{}'.format(prourl.get('zone')),
    )
    print('up_manage finished')


def roback(project, username):
    condb('UPDATE `project` SET `lock`=1 WHERE `name`="{}";'.format(project))
    ipaddress = serverip(project)
    ssh = comupload(ipaddress)
    res = ssh.comand(
        'tar xf /sitebackup/{project}/{project}_$(date +%F).tar.gz -C /sitebackup/{project} && rm -fr /var/www/html/{project} && mv /sitebackup/{project}/{project} /var/www/html/ && echo -n true || echo -n false'.format(
            project=project
        )
    )
    ssh.sshclose()
    if 'true' in res:
        condb(
            'UPDATE `project` SET `user`="{}",`status` = 3,`ctime` = NOW(),`lock`=NULL,`rolback`=NULL WHERE `name`="{}";'.format(
                username, project
            )
        )
        condb(
            'INSERT INTO `uploadlog` (proname,username,ctime,stat) VALUES ("%s","%s",NOW(),2);'
            % (project, username)
        )


if __name__ == "__main__":
    # create_local('wakastar')
    # up_data('wakastar', 'cj')
    # create_manage('wakastar')
    # up_manage('wakastar', 'chenjing')
    res = subprocess.run('ls')
    print(res.returncode)
    print(res.stdout)
    print(res.stderr)
