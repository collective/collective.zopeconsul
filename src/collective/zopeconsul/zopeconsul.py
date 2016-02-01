# -*- coding: utf-8 -*-
from AccessControl import getSecurityManager
from Queue import Empty
from Queue import Queue
from collective.zopeconsul.interfaces import ITaskQueue
from plone.memoize import forever
from transaction import get as get_transaction
from transaction.interfaces import ISavepoint
from transaction.interfaces import ISavepointDataManager
from zope.component import ComponentLookupError
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
import logging
import urllib
import urlparse
import uuid
import consul

logger = logging.getLogger('collective.zopeconsul')

_marker = object()


class DummySavepoint:
    implements(ISavepoint)

    valid = property(lambda self: self.transaction is not None)

    def __init__(self, datamanager):
        self.datamanager = datamanager

    def rollback(self):
        pass


class ConsulSendTransactionDataManager(object):

    implements(ISavepointDataManager)

    _COUNTER = 0

    def __init__(self, queue, task):
        self.queue = queue
        self.task = task

        self.sort_key = '~collective.zopeconsul.{0:d}'.format(
            ConsulSendTransactionDataManager._COUNTER)
        ConsulSendTransactionDataManager._COUNTER += 1

    def commit(self, t):
        pass

    def sortKey(self):
        return self.sort_key

    def abort(self, t):
        pass

    def tpc_begin(self, t):
        pass

    def tpc_vote(self, t):
        pass

    def tpc_finish(self, t):
        self.queue.put(self.task)

    def tpc_abort(self, t):
        pass

    def savepoint(self):
        return DummySavepoint(self)


class ConsulConfigSender(object):

    transaction_data_manager = ConsulSendTransactionDataManager


    def add(self, url=None, method='GET', params=None, headers=None,
            payload=_marker):
        task = lambda: send_vhm(url, host_map, platform)
        get_transaction().join(self.transaction_data_manager(self, task))
        return task_id


def send_vhm(url, host_map, platform):
    """We have to remap the VHM into something a bit more useful to a consul template"
    We are given hostmap[host][port] = path
    We will push to consul on each startup and VHM modifcation
        zope/vhm/*platform*/*host:port* -> host, port, regex, path
    It will remove any old hosts.

    Platform could be automatic based on hash of VHM or ZODB connections or some
    other unique aspect. Maybe a name stored in the root?
    """
    c = consul.Consul(url)

    prefix = "zope/vhm/"+platform

    old_values = c.kv.get('zope/vhm', recurse=True)
    c.kv.delete('zope/vhm', recurse=True)
    for host, ports in host_map.items():
        for port, path in ports.items():
            value = str( (host, port, None, path))
            c.kv.put("%s/%s:%s" % (prefix, host, port), value)




# need to monkey patch VHM as there are no events

def set_map(self, map_text, RESPONSE=None):
    res = self.__monkey__set_map(map_text, RESPONSE)
    ConsulConfigSender().send_vhm(self.sub_map)
