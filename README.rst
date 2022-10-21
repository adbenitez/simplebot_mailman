Mailman SimpleBot plugin
========================

.. image:: https://img.shields.io/pypi/v/simplebot_mailman.svg
   :target: https://pypi.org/project/simplebot_mailman

.. image:: https://img.shields.io/pypi/pyversions/simplebot_mailman.svg
   :target: https://pypi.org/project/simplebot_mailman

.. image:: https://pepy.tech/badge/simplebot_mailman
   :target: https://pepy.tech/project/simplebot_mailman

.. image:: https://img.shields.io/pypi/l/simplebot_mailman.svg
   :target: https://pypi.org/project/simplebot_mailman

.. image:: https://github.com/adbenitez/simplebot_mailman/actions/workflows/python-ci.yml/badge.svg
   :target: https://github.com/adbenitez/simplebot_mailman/actions/workflows/python-ci.yml

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

`SimpleBot`_ plugin that allows to subscribe to `Mailman`_ mailing lists using Delta Chat.

Install
-------

To install run::

  pip install simplebot-mailman

Customization
-------------

To set the URL of the Mailman REST API::

  simplebot -a bot@example.com db -s simplebot_mailman/api_url http://localhost:8001/3.1/

To set the username of the Mailman REST API::

  simplebot -a bot@example.com db -s simplebot_mailman/api_username restadmin

To set the password of the Mailman REST API::

  simplebot -a bot@example.com db -s simplebot_mailman/api_password MyStrongPassword

To set the domain used to create new mailing lists::

  simplebot -a bot@example.com db -s simplebot_mailman/domain example.com


.. _SimpleBot: https://github.com/simplebot-org/simplebot
.. _Mailman: https://www.list.org
