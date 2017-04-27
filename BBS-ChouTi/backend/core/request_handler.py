#!/usr/bin/env python
# -*- coding:utf-8 -*-
import tornado.web
from backend.session.session import SessionFactory


class BaseRequestHandler(tornado.web.RequestHandler):
    # initialliza钩子函数，相当于父类的构造函数
    def initialize(self):

        self.session = SessionFactory.get_session_obj(self)
