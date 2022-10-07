import pymysql


def condb(sql):
    '''
    :param sql: 要执行的sql语句
    :return: 一条记录和多条记录
    '''
    conn = pymysql.connect(host='172.18.188.5', user='root', password='123456',
                           database='southpark', charset='utf8', port=3306)
    # 得到一个可以执行SQL语句并且将结果作为字典返回的游标(默认返回的结果为元组)
    local_cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    if 'SELECT' in sql:
        local_cursor.execute(sql)
        # 返回结果为字典格式,fetchone()返回一条记录
        local_one = local_cursor.fetchone()
        if local_one:
            # 返回结果为字典格式,fetchall()返回多条记录
            local_all = local_cursor.fetchall()
            local_all.insert(0, local_one)
        else:
            local_all = []
        local_cursor.close()
        conn.close()
        return local_one, local_all
    elif 'UPDATE' or 'INSERT' in sql:
        try:
            local_one = local_cursor.execute(sql)
            local_all = None
            conn.commit()
            local_cursor.close()
            conn.close()
            return local_one, local_all
        except Exception as f:
            # Rollback in case there is any error
            print(f)
            conn.rollback()
        local_cursor.close()
        conn.close()
