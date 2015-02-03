:mod:`ayame` --- Core API
=========================

.. module:: ayame


Application
-----------

.. class:: Ayame(name)

   .. attribute:: config
   .. attribute:: context
   .. attribute:: environ
   .. attribute:: request
   .. attribute:: session

   .. method:: __call__(environ, start_response)
   .. method:: handle_request(object)
   .. method:: handle_error(error)
   .. method:: forward(object, values=None, anchor=None)
   .. method:: redirect(object, values=None, anchor=None, permanent=False)
   .. method:: uri_for(object, values=None, anchor=None, method=None, query=True, relative=False)


.. class:: Request(environ, values)

   .. attribute:: environ
   .. attribute:: method
   .. attribute:: uri
   .. attribute:: query
   .. attribute:: form_data
   .. attribute:: path
   .. attribute:: locale
   .. attribute:: input
   .. attribute:: session


Components
----------

.. class:: Component(id, model=None)

   .. attribute:: id
   .. attribute:: model
   .. attribute:: model_object
   .. attribute:: parent
   .. attribute:: escape_model_string
   .. attribute:: render_body_only
   .. attribute:: visible
   .. attribute:: behaviors
   .. attribute:: app
   .. attribute:: config
   .. attribute:: environ
   .. attribute:: request
   .. attribute:: session

   .. method:: add(*args)
   .. method:: converter_for(value)
   .. method:: element()
   .. method:: forward(*args, **kwargs)
   .. method:: iter_parent(class_=None)
   .. method:: model_object_as_string()
   .. method:: page()
   .. method:: path()
   .. method:: redirect(*args, **kwargs)
   .. method:: fire()
   .. method:: on_fire()
   .. method:: render(element)
   .. method:: on_configure()
   .. method:: on_before_render()
   .. method:: on_render(element)
   .. method:: on_after_render()
   .. method:: tr(key, component=None)
   .. method:: uri_for(*args, **kwargs)

.. class:: MarkupContainer()

   *bases*: :py:class:`ayame.Component`

   .. attribute:: markup_type
   .. attribute:: children
   .. attribute:: has_markup
   .. attribute:: head

   .. method:: add(*args)
   .. method:: find(path)
   .. method:: walk(step=None)
   .. method:: fire()
   .. method:: on_configure()
   .. method:: on_before_render()
   .. method:: on_render(element)
   .. method:: on_render_element(element)
   .. method:: on_render_attrib(element)
   .. method:: render_component(element)
   .. method:: on_after_render()
   .. method:: load_markup()
   .. method:: find_head(root)

.. class:: Page()

   *bases*: :py:class:`ayame.MarkupContainer`

   .. attribute:: status
   .. attribute:: headers

   .. method:: __call__()
   .. method:: render()

.. decorator:: nested


Behaviors
---------

.. data:: AYAME_PATH

.. class:: Behavior()

   .. attribute:: component
   .. attribute:: app
   .. attribute:: config
   .. attribute:: environ
   .. attribute:: request
   .. attribute:: session

   .. method:: forward(*args, **kwargs)
   .. method:: on_configure(component)
   .. method:: on_before_render(component)
   .. method:: on_component(component, element)
   .. method:: on_after_render(component)
   .. method:: redirect(*args, **kwargs)
   .. method:: uri_for(*args, **kwargs)

.. class:: AttributeModifier(attr, model)

   *bases*: :py:class:`ayame.Behavior`

   .. method:: on_component(component, element)
   .. method:: new_value(value, new_value)


Exceptions
----------

.. exception:: AyameError

.. exception:: ComponentError

.. exception:: ConversionError

   .. attribute:: converter
   .. attribute:: value
   .. attribute:: type

.. exception:: MarkupError

.. exception:: RenderingError

.. exception:: ResourceError

.. exception:: RouteError

.. exception:: ValidationError

   .. attribute:: component
   .. attribute:: keys
   .. attribute:: vars
