# -*- coding: utf-8 -*-
from collective.zopeconsul.taskqueue import LocalVolatileTaskQueue as local

from collective.zopeconsul.config import HAS_REDIS
from collective.zopeconsul.config import HAS_MSGPACK

if HAS_REDIS and HAS_MSGPACK:
    from collective.zopeconsul.redisqueue import RedisTaskQueue as redis
