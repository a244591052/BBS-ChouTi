#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Session类型：cache/redis/memcached
SESSION_TYPE = "redis"
# Session超时时间（秒）
SESSION_EXPIRES = 20*60

LOGIN_URL = '/login'