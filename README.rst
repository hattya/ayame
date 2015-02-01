Ayame
=====

Ayame is a component based WSGI framework. It is inspired by
`Apache Wicket`_, `Apache Click`_ and Flask_.

.. image:: https://pypip.in/version/ayame/badge.svg
   :target: https://pypi.python.org/pypi/ayame

.. image:: https://drone.io/github.com/hattya/ayame/status.png
   :target: https://drone.io/github.com/hattya/ayame/latest

.. image:: https://ci.appveyor.com/api/projects/status/67nbqb4ej84liu9m?svg=true
   :target: https://ci.appveyor.com/project/hattya/ayame

.. _Apache Wicket: http://wicket.apache.org/
.. _Apache Click: http://click.apache.org/
.. _Flask: http://flask.pocoo.org/


Requirements
------------

- Python 2.7 or 3.3+
- Werkzeug


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
            super(HelloWorld, self).__init__()
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
