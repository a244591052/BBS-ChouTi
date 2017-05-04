#!/usr/bin/env python
# -*- coding:utf-8 -*-
import config
from hashlib import sha1
import os
import time,json

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

# 创建一个CacheSession, 有一个问题就是服务器端的session缓存没有过期时间，肯定会越来越大直到内存极限
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
    session_container = {}
    session_id = "__sessionId__"
    import memcache
    conn = memcache.Client(['127.0.0.1:11211'], debug=0, cache_cas=True)

    def __init__(self, handler):
        self.handler = handler
        # 获取session值
        client_random_str = handler.get_cookie(MemcachedSession.session_id, None)
        # 如果有值且在服务器端的session列表中
        if client_random_str and MemcachedSession.conn.get(client_random_str):
            self.random_str = client_random_str
            MemcachedSession.conn.set(self.random_str, MemcachedSession.conn.get(self.random_str), config.SESSION_EXPIRES)
        # 如果不存在值则新建
        else:
            self.random_str = create_session_id()
            MemcachedSession.conn.set(self.random_str, json.dumps({}), config.SESSION_EXPIRES)

        # 设置超时时间
        expires_time = time.time() + config.SESSION_EXPIRES
        handler.set_cookie(CacheSession.session_id, self.random_str, expires=expires_time)
    # 便于使用的封装
    def __getitem__(self, key):
        session = MemcachedSession.conn.get(self.random_str)
        ret = json.loads(session)
        ret = ret.get(key, None)
        return ret

    def __setitem__(self, key, value):
        session = MemcachedSession.conn.get(self.random_str)
        ret = json.loads(session)
        ret[key] = value
        MemcachedSession.conn.set(self.random_str, json.dumps(ret), config.SESSION_EXPIRES)

    def __delitem__(self, key):
        session = MemcachedSession.conn.get(self.random_str)
        ret = json.loads(session)
        del ret[key]
        MemcachedSession.conn.set(self.random_str, json.dumps(ret), config.SESSION_EXPIRES)