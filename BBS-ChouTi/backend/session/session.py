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


# 返回的是字节类型，所以需要进行字节字符转换, 还有就是数据类型存进去都会变成字节类型，所以需要进行json转换
class RedisSession:
    # session_container = {}
    session_id = "__sessionId__"
    import redis
    pool = redis.ConnectionPool(host='127.0.0.1', port=6379)
    r = redis.Redis(connection_pool=pool)

    def __init__(self, handler):
        self.handler = handler
        # 获取session值
        client_random_str = handler.get_cookie(RedisSession.session_id, None)
        # 如果有值且在服务器端的session列表中
        if client_random_str and RedisSession.r.exists(client_random_str):
            self.random_str = client_random_str

        # 如果不存在值则新建
        else:
            self.random_str = create_session_id()
            RedisSession.r.hset(self.random_str, None, None)

        # 设置超时时间
        RedisSession.r.expire(self.random_str, config.SESSION_EXPIRES)

        expires_time = time.time() + config.SESSION_EXPIRES
        handler.set_cookie(RedisSession.session_id, self.random_str, expires=expires_time)

    # 便于使用的封装
    def __getitem__(self, key):
        """
        因为取出来都是字节，所以需要首先转化为字符，接着看能不能转化为数据类型
        :param key:
        :return:
        """
        result = RedisSession.r.hget(self.random_str, key)
        if result:
            ret_str = str(result, encoding="utf-8")
            try:
                result = json.loads(ret_str)
            except:
                result = ret_str
            return result
        else:
            return result

    def __setitem__(self, key, value):
        """
        这里很容易出错的一点就是字典的单双引号，当我们把key弄成单引号的时候json会出错
        所以这里碰到dict类型，我们主动用json封装，这样json就会自动做引号处理，再取出来的时候
        就不会出错了
        :param key:
        :param value:
        :return:
        """
        if type(value) == dict:
            RedisSession.r.hset(self.random_str, key, json.dumps(value))
        else:
            RedisSession.r.hset(self.random_str, key, value)

    def __delitem__(self, key):
        RedisSession.r.hdel(self.random_str, key)


# 只支持字符串类型，所以涉及到别的python类型时需要json转换
class MemcachedSession:
    # session_container = {}
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