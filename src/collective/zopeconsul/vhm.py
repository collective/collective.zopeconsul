# -*- coding: utf-8 -*-
import logging

from consulserver import Consul
from transaction import get as get_transaction
from transaction.interfaces import ISavepoint, ISavepointDataManager
from zope.app.publication.zopepublication import ZopePublication
from zope.interface import implements

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

    def send_vhm(self, host_map):
        task = lambda: send_vhm(host_map)
        get_transaction().join(self.transaction_data_manager(task))
        return


def send_vhm(host_map, consul=None):
    """
    We have to remap the VHM into something a bit more useful to a consul
    template.
    We are given hostmap[host][port] = path
    It will remove any old hosts.
    """
    if consul is None:
        consul = Consul()
    if consul.ignore:
        logger.info('Not setting vhm values in consul (CONSUL_IGNORE = 1)')
        return
    logger.info('Setting consul vhm values')
    server = consul.server
    vhm = consul.key_base('vhm')
    old_values = server.kv.get(vhm, recurse=True)
    if old_values:
        server.kv.delete(vhm, recurse=True)
    for host in host_map:
        for nothing, values in host_map[host].items():
            server.kv.put('%s/%s' % (vhm, host), '%s' % '/'.join(values))


# need to monkey patch VHM as there are no events
def set_map(self, map_text, RESPONSE=None):
    self._old_set_map(map_text, RESPONSE)
    ConsulConfigSender().send_vhm(self.fixed_map)


def set_vhm(event, consul):
    db = event.database
    connection = db.open()
    root = connection.root()
    root_folder = root.get(ZopePublication.root_name)
    vhm = root_folder.virtual_hosting
    if hasattr(vhm, 'fixed_map'):
        send_vhm(vhm.fixed_map, consul=consul)
