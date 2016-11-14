..
    :copyright: Copyright (c) 2016 Postmodern Digital

.. _installing:

**********
Installing
**********


Installing with pip
===================

.. highlight:: bash

Installation is simple with `pip <http://www.pip-installer.org/>`_::

    pip install ftrack-connect-houdini

.. note::

    This project is not yet available on PyPi.

Building from source
====================

You can also build manually from the source for more control. First obtain a
copy of the source by either downloading the
`zipball <https://bitbucket.org/ftrack/ftrack-connect-houdini/get/master.zip>`_ or
cloning the public repository::

    git clone git@bitbucket.org:postmodern_dev/ftrack-connect-houdini.git

Then you can build and install the package into your current Python
site-packages folder::

    python setup.py install

Alternatively, just build locally and manage yourself::

    python setup.py build

Building documentation from source
----------------------------------

To build the documentation from source::

    python setup.py build_sphinx

Then view in your browser::

    file:///path/to/ftrack-connect-houdini/build/doc/html/index.html

Dependencies
============

* `Python <http://python.org>`_ >= 2.6, < 3
* `ftrack connect <https://bitbucket.org/ftrack/ftrack-connect>`_ >= 0.1.2, < 2
* `houdini <http://www.autodesk.com/products/houdini/overview>`_ >= 2014, <= 2016

Additional For building
-----------------------

* `Sphinx <http://sphinx-doc.org/>`_ >= 1.2.2, < 2
* `sphinx_rtd_theme <https://github.com/snide/sphinx_rtd_theme>`_ >= 0.1.6, < 1
