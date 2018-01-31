=====================
collective.zopeconsul
=====================

*collective.zopeconsul* enables asynchronous sending of zope configuration
to consul. It sends the VHM domain information to consul along
with port and ip address of this instance. It can also be used to set key/value
pairs from buildout config options or environment variables.

Configuration
--------------

zopeconsul can be configured by adding the following to your buildout:

.. code:: ini

  [instance]
  eggs = collective.zopeconsul

  zope-conf-additional =
    <product-config zopeconsul>
      consul_url http://localhost:8500
      consul_prefix zope
      consul_key_somename somevalue
    </product-config>

Any configuration option can be overridden by an environment variable:

.. code:: ini

  $ export CONSUL_URL=http://localhost:8500
  $ export CONSUL_KEY_SOMENAME=somevalue

Configuration options
---------------------

consul_url
    Url of the consul server to connect to. *Default: http\://localhost:8500*

consul_prefix
    When setting key/values, this is the base key from which all values are
    set. *Default: zope*

consul_instancename
    Gives a name to the instance. Instead of values being placed in ``<consul_prefix>``, they are placed in ``<consul_prefix>/instances/<instance_name>`` on the consul server. Useful when there are multiple instances being orchestrated from consul. *Default: unset*

consul_key_[name]
    Allows to set arbitrary key values with any name. *Example: ``consul_key_somekey = somevalue``*

consul_ignore
    Skips setting consul key values. Useful if you have multiple instances that
    share the same code. You can set this value on specific instances and no
    key/values will be set in consul.
