# -*- coding: utf-8 -*-
from zope.app.publication.zopepublication import ZopePublication
from zope.component.hooks import getSite
import os
import urllib
from urlparse import urlsplit
from transaction import get as get_transaction
from transaction.interfaces import ISavepoint
from transaction.interfaces import ISavepointDataManager
from zope.interface import implements
import logging
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

    def __init__(self, task):
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
        self.task()

    def tpc_abort(self, t):
        pass

    def savepoint(self):
        return DummySavepoint(self)


class ConsulConfigSender(object):

    transaction_data_manager = ConsulSendTransactionDataManager


    def send_vhm(self, host_map, platform="zope"):
        #TODO: get from zope config
        task = lambda: send_vhm(host_map, platform)
        get_transaction().join(self.transaction_data_manager(task))
        return


def send_vhm(host_map, platform="zope"):
    """We have to remap the VHM into something a bit more useful to a consul template"
    We are given hostmap[host][port] = path
    We will push to consul on each startup and VHM modifcation
        zope/vhm/*platform*/*host:port* -> host, port, regex, path
    It will remove any old hosts.

    Platform could be automatic based on hash of VHM or ZODB connections or some
    other unique aspect. Maybe a name stored in the root?
    """
    from App.config import getConfiguration
    config = getConfiguration()
    url = os.environ.get('CONSUL_URL', 'http://localhost:8500')
    if url is not None:
        r =  urlsplit(url)
        c = consul.Consul(scheme=r.scheme, host=r.hostname, port=r.port)
    else:
        c = consul.Consul()

    prefix = "zope/vhm/"+platform

    old_values = c.kv.get('zope/vhm', recurse=True)
    c.kv.delete('zope/vhm', recurse=True)
    count = 0
    logger.debug(host_map)
    for host, ports in host_map.items():
        for port, path in ports.items():
            value = str( (host, port, None, path))
            c.kv.put("%s/%s:%s" % (prefix, host, port), value)
            count += 1
    logger.info("Updated consul %s with %i values" % (url, count))




# need to monkey patch VHM as there are no events

def set_map(self, map_text, RESPONSE=None):
    res = self._old_set_map(map_text, RESPONSE)
    ConsulConfigSender().send_vhm(self.fixed_map)

def notifyStartup(event):
    db = event.database
    connection = db.open()
    root = connection.root()
    root_folder = root.get(ZopePublication.root_name)
    vhm = root_folder.virtual_hosting
    send_vhm(vhm.fixed_map)