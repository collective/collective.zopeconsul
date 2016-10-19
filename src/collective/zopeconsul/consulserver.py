import logging
import os
import re
from urlparse import urlsplit

import consul
from App.config import getConfiguration

logger = logging.getLogger('collective.zopeconsul')


class Consul(object):

    def __init__(self):
        self.conf = getConfiguration().product_config.get('zopeconsul', dict())
        self.url = self.getconf('consul_url')
        r = urlsplit(self.url)
        self.server = consul.Consul(scheme=r.scheme,
                                    host=r.hostname,
                                    port=r.port)
        self.instance = self.getconf('consul_instancename', None)
        self.prefix = self.getconf('consul_prefix', 'zope/')
        self.ignore = self.getconf('consul_ignore', 0)

    def getconf(self, name, default=None):
        value = os.environ.get(name.upper(), None)
        if value is None:
            value = self.conf.get(name, default)
        return value

    def key_base(self, name):
        """ Sets the base of where key/values are stored in consul.
        Default value is:
            <self.prefix>/<name>
        If consul_instancename option is set, values are stored at:
            <self.prefix>/machines/<consul_instancename>/<name>
        self.prefix defaults to zope
        """
        return "%s/%s%s" % (self.prefix.strip('/'),
                             (self.instance is not None
                              and 'instances/%s/' % self.instance
                              or ''),
                             name.strip('/'))


def set_keyvalues(event, consulsrv):
    """ Set any key values starting with CONSUL_KEY_
        Start with values from the configuration, then override with env vars.
    """
    if consulsrv.ignore:
        logger.info("Not setting any consul values (CONSUL_IGNORE = 1)")
        return

    logger.info('Setting consul values')
    values = {}
    for i in consulsrv.conf.keys():
        if i.startswith('consul_key'):
            build_keyvalues(i, consulsrv.conf.get(i), values)

    for i in os.environ.keys():
        if i.startswith('CONSUL_KEY_'):
            build_keyvalues(i.lower(), os.environ.get(i), values)

    for i in values:
        consulsrv.server.kv.put('%s/%s' % (consulsrv.key_base('conf'), i),
                                values[i])


def build_keyvalues(key, keyval, values):
    newkey = re.sub('consul_key_', '', key)
    newkey = re.sub('_', '/', newkey)
    values[newkey] = keyval
