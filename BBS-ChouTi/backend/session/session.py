#!/usr/bin/env python
# -*- coding:utf-8 -*-
import config
from hashlib import sha1
import os
import time

# 随机生成字符串加密成Session id
create_session_id = lambda: sha1(bytes('%s%s' % (os.urandom(16), time.time()), encoding='utf-8')).hexdigest()




class SessionFactory:

    @staticmethod
    def get_session_obj(handler):
        obj = None

        if config.SESSION_TYPE == "cache":
            obj = CacheSession(handler)
        elif config.SESSION_TYPE == "memcached":
            obj = MemcachedSession(handler)
        elif config.SESSION_TYPE == "redis":
            obj = RedisSession(handler)
        return obj

# 创建一个Session
class CacheSession:
    session_container = {}
    session_id = "__sessionId__"

    def __init__(self, handler):
        self.handler = handler
        # 获取session值
        client_random_str = handler.get_cookie(CacheSession.session_id, None)
        # 如果有值且在服务器端的session列表中
        if client_random_str and client_random_str in CacheSession.session_container:
            self.random_str = client_random_str
        # 如果不存在值则新建
        else:
            self.random_str = create_session_id()
            CacheSession.session_container[self.random_str] = {}

        # 设置超时时间
        expires_time = time.time() + config.SESSION_EXPIRES
        handler.set_cookie(CacheSession.session_id, self.random_str, expires=expires_time)
    # 便于使用的封装
    def __getitem__(self, key):
        ret = CacheSession.session_container[self.random_str].get(key, None)
        return ret

    def __setitem__(self, key, value):
        CacheSession.session_container[self.random_str][key] = value

    def __delitem__(self, key):
        if key in CacheSession.session_container[self.random_str]:
            del CacheSession.session_container[self.random_str][key]


class RedisSession:
    def __init__(self, handler):
        pass


class MemcachedSession:
    def __init__(self, handler):
        pass