#!/usr/bin/python3
# -*- coding:utf-8 -*-

from gevent import monkey  # 解决requests  post请求递归次数太多的问题，一定要在导入gevent模块前导入

monkey.patch_all()

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from views import app

if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
