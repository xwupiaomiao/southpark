import requests, json


def reports(username, msge, ctime, url=' '):
    data = {"msg_type": "post", "content": {"post": {
        "zh_cn": {"title": "SP平台通知", "content": [
            [{"tag": "text", "text": "%s" % (username)}],
            [{"tag": "text", "text": "%s" % (msge)}],
            [{"tag": "text", "text": "链接：%s" % (url)}],
            [{"tag": "text", "text": "时间：%s" % (ctime)}]
        ]}}}}
    headers = {"Content-Type": "application/json"}
    requests.post(url='https://open.feishu.cn/open-apis/bot/v2/hook/709bd2fb-d2cc-4b57-84cd-41b425dbd68e',
                  headers=headers, data=json.dumps(data))


def reportdns(username, proxy, url, ctime, status, newip, oldip=None):
    data = {"msg_type": "post", "content": {"post": {
        "zh_cn": {"title": "DNS通知", "content": [
            [{"tag": "text", "text": "用户：%s" % (username)}],
            [{"tag": "text", "text": "代理：%s" % (proxy)}],
            [{"tag": "text", "text": "链接：%s" % (url)}],
            [{"tag": "text", "text": "时间：%s" % (ctime)}],
            [{"tag": "text", "text": "状态：%s" % (status)}],
            [{"tag": "text", "text": "绑定IP：%s" % (newip)}],
            [{"tag": "text", "text": "原绑定IP：%s" % (oldip)}]
        ]}}}}
    headers = {"Content-Type": "application/json"}
    requests.post(url='https://open.feishu.cn/open-apis/bot/v2/hook/cacd48ff-16d3-44fa-94e7-f082fdd5907e',
                  headers=headers, data=json.dumps(data))


def reportsasset(username, job, ctime, status=None, device=None):
    if status:
        data = {"msg_type": "post", "content": {"post": {
            "zh_cn": {"title": "入职通知", "content": [
                [{"tag": "text", "text": "姓名：%s" % (username)}],
                [{"tag": "text", "text": "岗位：%s" % (job)}],
                [{"tag": "text", "text": "入职时间：%s" % (ctime)}],
                [{"tag": "text", "text": "使用设备：%s" % (device)}]
            ]}}}}
    else:
        data = {"msg_type": "post", "content": {"post": {
            "zh_cn": {"title": "离职通知", "content": [
                [{"tag": "text", "text": "姓名：%s" % (username)}],
                [{"tag": "text", "text": "岗位：%s" % (job)}],
                [{"tag": "text", "text": "离职时间：%s" % (ctime)}]
            ]}}}}
    headers = {"Content-Type": "application/json"}
    requests.post(url='https://open.feishu.cn/open-apis/bot/v2/hook/ee86858c-4306-4f8a-97b2-9c48295a31d4',
                  headers=headers, data=json.dumps(data))


if __name__ == '__main__':
    reportsasset('刘思利', '前端开发', '2022-3-11', False)
