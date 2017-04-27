#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
import functools
import config
from backend.utils.response import BaseResponse





# 正常form请求之类的跳转装饰器
def auth_login_redirect(func):

    def inner(self, *args, **kwargs):
        if not self.session['is_login']:
            self.redirect(config.LOGIN_URL)
            return
        func(self, *args, **kwargs)
    return inner

# AJAX请求的装饰器，因为AJAX请求服务器页面跳转无效，所以只能在浏览器上进行判断跳转
def auth_login_json(func):

    def inner(self, *args, **kwargs):
        if not self.session['is_login']:
            rep = BaseResponse()
            rep.summary = "auth failed"
            self.write(json.dumps(rep.__dict__))
            return
        func(self, *args, **kwargs)
    return inner
