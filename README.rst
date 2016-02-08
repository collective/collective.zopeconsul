collective.zopeconsul
====================

.. image:: https://secure.travis-ci.org/collective/collective.zopeconsul.png
   :target: http://travis-ci.org/collective/collective.zopeconsul

*collective.zopeconsul* enables asynchronous sending of zope configuration
to consul. It sends the VHM domain information to consul along
with port and ip address of this instance.

Minimal configuration:

.. code:: ini
  $ export CONSUL_URL=http://localhost:8500

or (TODO)

.. code:: ini

   zope-conf-additional =
       %import collective.zopeconsul
       <zopeconsul >
       url consul://localhost
       prefix zope/vhm/prod
       </zopeconsul>

Alternatively environment variables can be used

