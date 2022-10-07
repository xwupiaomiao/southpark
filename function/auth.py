#!/usr/bin/python3
# -*- coding: utf-8 -*-


import json
import ssl
from ldap3 import ALL_ATTRIBUTES, ALL
from ldap3 import Connection, NTLM, Server, ServerPool, SUBTREE
from .conndb import condb
from ldap3 import MODIFY_REPLACE

server1 = Server("172.17.0.100", port=636, use_ssl=True, get_info=ALL, connect_timeout=2)

LDAP_SERVER_POOL = [server1]
SERVER_USER = 'southpark\\administrator'
SERVER_PASSWORD = "123456"


class AD(object):
    '''    
    AD用户操作    
    '''

    def __init__(self):
        '''初始化'''
        self.conn = Connection(  # 配置服务器连接参数
            server=LDAP_SERVER_POOL,
            auto_bind=True,
            authentication=NTLM,  # 连接Windows AD需要配置此项
            read_only=False,  # 禁止修改数据：True
            user=SERVER_USER,  # 管理员账户
            password=SERVER_PASSWORD,
        )
        self.active_base_dn = 'ou=south,dc=southpark,dc=com'  # 正式员工账户所在OU
        self.search_filter = '(objectclass=user)'  # 只获取【用户】对象
        self.ou_search_filter = '(objectclass=organizationalUnit)'  # 只获取【OU】对象

    def users_get(self):
        '''获取所有的用户'''
        self.conn.search(search_base=self.active_base_dn, search_filter=self.search_filter, attributes=ALL_ATTRIBUTES)
        res = self.conn.response_to_json()
        res = json.loads(res)['entries']
        return res

    def OU_get(self):
        '''获取所有的OU'''
        self.conn.search(search_base=self.active_base_dn, search_filter=self.ou_search_filter,
                         attributes=ALL_ATTRIBUTES)
        res = self.conn.response_to_json()
        res = json.loads(res)['entries']
        return res

    def create_obj(self, dn, type, attr=None):
        '''
        新建用户or 部门，User需要设置密码，激活账户
        :param dn: dn = "ou=人事部3,ou=罗辑实验室,dc=adtest,dc=intra"  # 创建的OU的完整路径
                   dn = "cn=张三,ou=人事部3,ou=罗辑实验室,dc=adtest,dc=intra"  # 创建的User的完整路径
        :param type:选项：ou or user
        :param attr = {#User 属性表，需要设置什么属性，增加对应的键值对
                        "SamAccountName": "zhangsan",  # 账号
                        "EmployeeID":"1",    # 员工编号
                        "Sn": "张",  # 姓
                        "name": "张三",
                        "telephoneNumber": "12345678933",
                        "mobile": "12345678933",
                        "UserPrincipalName":"zhangsan@adtest.com",
                        "Mail":"zhangsan@adtest.com",
                        "Displayname": "张三",
                        "Manager":"CN=李四,OU=人事部,DC=adtest,DC=com",#需要使用用户的DN路径
                    }
                attr = {#OU属性表
                        'name':'人事部',
                        'managedBy':"CN=张三,OU=IT组,OU=罗辑实验室,DC=adtest,DC=intra", #部分负责人
                        }
        :return:True and success 是创建成功了
        (True, {'result': 0, 'description': 'success', 'dn': '', 'message': '', 'referrals': None, 'type': 'addResponse'})
        '''
        object_class = {'user': ['user', 'posixGroup', 'top'],
                        'ou': ['organizationalUnit', 'posixGroup', 'top'],
                        }
        res = self.conn.add(dn=dn, object_class=object_class[type], attributes=attr)
        if type == "user":  # 如果是用户时，我们需要给账户设置密码，并把账户激活
            self.conn.extend.microsoft.modify_password(dn, "123456")  # 设置用户密码
            self.conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, ['66048'])]})  # 激活用户
            self.conn.unbind()
        return res, self.conn.result

    def del_obj(self, DN):
        '''
        删除用户 or 部门
        :param DN:
        :return:True
        '''
        res = self.conn.delete(dn=DN)
        self.conn.unbind()
        return res

    def __rename_obj(self, dn, newname):
        '''
        OU or User 重命名方法
        :param dn:需要修改的object的完整dn路径
        :param newname: 新的名字，User格式："cn=新名字";OU格式："OU=新名字"
        :return:返回中有：'description': 'success', 表示操作成功
        {'result': 0, 'description': 'success', 'dn': '', 'message': '', 'referrals': None, 'type': 'modDNResponse'}
        '''
        self.conn.modify_dn(dn, newname)
        return self.conn.result

    def clock_unclock(self, dn, clock):
        """
        启用帐号：66048 为密码永不过期及启用帐号，单启用帐号为 512
        self.conn.modify(CN, {'userAccountControl': [(MODIFY_REPLACE, ['66048'])]})
        禁用帐号：66050 为密码永不过期及禁用帐号，单禁用帐号为 514
        self.conn.modify(CN, {'userAccountControl': [(MODIFY_REPLACE, ['66050'])]})
        :param dn: 'CN=李四,OU=south,DC=southpark,DC=com'
        :param clock: true为解锁账号，false为禁用账号
        :return:
        """
        if clock:
            self.conn.modify(dn, {'userAccountControl': [('MODIFY_REPLACE', ['66048'])]})
            self.conn.unbind()
            return self.conn.result
        else:
            self.conn.modify(dn, {'userAccountControl': [('MODIFY_REPLACE', ['66050'])]})
            self.conn.unbind()
            return self.conn.result

    def changpwd(self, username, password, newpassworld):
        res, chinesename, userau = self.auth(username, password)
        if res:
            dn = 'CN=%s,OU=south,DC=southpark,DC=com' % (chinesename)
            self.conn.extend.microsoft.modify_password(dn, newpassworld)
            return True
        else:
            return False

    def auth(self, username, password):
        """
        用户认证接口 #
        """
        ldap_user = '\\{}'.format(username)
        # server = Server('south.southpark.com', use_ssl=False)
        connection = Connection(server=LDAP_SERVER_POOL, user=ldap_user, password=password, authentication=NTLM)
        connection.bind()
        res = connection.search(
            search_base="ou=south,dc=southpark,dc=com",
            search_filter='(sAMAccountName={})'.format(username),
            search_scope=SUBTREE,
            attributes=['cn', 'givenName', 'mail', 'sAMAccountName', 'memberOf'],
            paged_size=5
        )
        if res:
            entry = connection.response[0]
            attr_dict = entry['attributes']
            manager = 0
            upload = 0
            video = 0
            game = 0
            domain = 0
            advert = 0
            image = 0
            engineer = 0
            loadpage = 0
            assets = 0
            for i in attr_dict.get('memberof'):
                if 'manager' in i:
                    manager = 1
                elif 'upload' in i:
                    upload = 1
                elif 'video' in i:
                    video = 1
                elif 'game' in i:
                    game = 1
                elif 'domain' in i:
                    domain = 1
                elif 'advert' in i:
                    advert = 1
                elif 'image' in i:
                    image = 1
                elif 'engineer' in i:
                    engineer = 1
                elif 'loadpage' in i:
                    loadpage = 1
                elif 'assets' in i:
                    assets = 1
            resuser, userall = condb('SELECT `loginuser` FROM userauthor WHERE `loginuser`="{}";'.format(
                attr_dict.get('sAMAccountName')))
            if resuser:
                condb(
                    "UPDATE `userauthor` SET `manager` = '{}',`upload` = '{}',`video` = '{}',`game` = '{}',`domain` = '{}',`advert` = '{}',`image` = '{}',`engineer` = '{}',`loadpage` = '{}',`assets`='{}' WHERE `loginuser`='{}';".format(
                        manager, upload, video, game, domain, advert, image, engineer,
                        loadpage, assets, attr_dict.get('sAMAccountName')))
            else:
                condb(
                    "INSERT INTO `userauthor` (loginuser,chinesename,manager,upload,video,game,`domain`,advert,`image`,`engineer`,`loadpage`,`assets`) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % (
                        attr_dict.get('sAMAccountName'), attr_dict.get('cn'), manager, upload,
                        video, game, domain, advert, image, engineer, loadpage, assets))
            userauthor, userauthorall = condb(
                'SELECT * FROM userauthor WHERE `loginuser`="{}";'.format(attr_dict.get('sAMAccountName')))
            connection.unbind()
            return (True, attr_dict.get('cn'), userauthor)
        else:
            connection.unbind()
            return (False, '账号已锁定或密码错误', None)


if __name__ == '__main__':
    attr = {
        'cn': '李四',
        'displayName': '李, 四',
        'distinguishedName': 'CN=李四,OU=south,DC=southpark,DC=com',
        'givenName': '四',
        'name': '李四',
        'objectCategory': 'CN=Person,CN=Schema,CN=Configuration,DC=southpark,DC=com',
        'sAMAccountName': 'ls',
        'sn': '李',
        'description': ['前端开发'],
    }
    rest = AD().create_obj('CN=李四,OU=south,DC=southpark,DC=com', 'user', attr)
    print(rest)
    # rest = AD().users_get()
    # print(rest)
    # AD().auth('yj', '123456')
    # AD().clock_unclock('CN=李四,OU=south,DC=southpark,DC=com', False)
