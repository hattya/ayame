Ayame
=====

Ayame is a component based WSGI framework. It is inspired by
`Apache Wicket`_, `Apache Click`_ and Flask_.

.. image:: https://img.shields.io/pypi/v/ayame.svg
   :target: https://pypi.org/project/ayame

.. image:: https://github.com/hattya/ayame/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/hattya/ayame/actions/workflows/ci.yml

.. image:: https://semaphoreci.com/api/v1/hattya/ayame/branches/master/badge.svg
   :target: https://semaphoreci.com/hattya/ayame

.. image:: https://ci.appveyor.com/api/projects/status/67nbqb4ej84liu9m?svg=true
   :target: https://ci.appveyor.com/project/hattya/ayame

.. image:: https://codecov.io/gh/hattya/ayame/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/hattya/ayame

.. _Apache Wicket: https://wicket.apache.org/
.. _Apache Click: https://click.apache.org/
.. _Flask: https://palletsprojects.com/p/flask


Requirements
------------

- Python 3.6+
- setuptools
- Werkzeug
- secure-cookie


Example Application
-------------------

::

    app.wsgi
    app/
        HelloWorld.html


app.wsgi
~~~~~~~~

.. code:: python

    from ayame import Ayame, Page
    from ayame.basic import Label


    class HelloWorld(Page):

        def __init__(self):
            super().__init__()
            self.add(Label('message', 'Hello World!'))


    application = Ayame(__name__)

    map = application.config['ayame.route.map']
    map.connect('/', HelloWorld)


HelloWorld.html
~~~~~~~~~~~~~~~

.. code:: html

    <?xml version="1.0"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml"
          xmlns:ayame="http://hattya.github.io/ayame">
      <head>
        <title>HelloWorld</title>
      </head>
      <body>
        <p ayame:id="message">...</p>
      </body>
    </html>


License
-------

Ayame is distributed under the terms of the MIT License.
