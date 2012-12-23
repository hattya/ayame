=====
ayame
=====


ayame is a component based WSGI framework. It is inspired by
`Apache Wicket`_, `Apache Click`_ and Flask_.


Requirements
------------

- Python 2.7 or 3.2
- Beaker

for testing

- nose
- coverage


Example Application
-------------------

::

    app.wsgi
    app/
        HelloWorld.html


app.wsgi
~~~~~~~~

.. code:: python

    from ayame.app import Ayame
    from ayame.basic import Label
    from ayame.core import Page


    class HelloWorld(Page):

        def __init__(self):
            super(HelloWorld, self).__init__()
            self.add(Label('message', 'Hello World!'))


    app = Ayame(__name__)
    map = app.config['ayame.route.map']
    map.connect('/', HelloWorld)


    application = app.new()


HelloWorld.html
~~~~~~~~~~~~~~~

.. code:: html

    <?xml version="1.0"?>
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml"
          xmlns:ayame="http://hattya.github.com/ayame">
      <head>
        <title>HelloWorld</title>
      </head>
      <body>
        <p ayame:id="message">...</p>
      </body>
    </html>


License
-------

ayame is distributed under the terms of the MIT License.


.. _Apache Wicket: http://wicket.apache.org/
.. _Apache Click: http://click.apache.org/
.. _Flask: http://flask.pocoo.org/
