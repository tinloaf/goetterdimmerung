Goetterdimmerung Configuration
===============================

.. _file_config:

This file specifies the possible configuration options for Goetterdimmerung. There also is a collection of :ref:`config examples <file_examples>`.

Global Options
--------------

entities
  List of entities to be controlled. See :ref:`Entity Configuration <conf_entity>`.
	**Type**: list of :ref:`entities <conf_entity>`.

attribute
  The name of the attribute to be controlled. This attribute is sent as service data in calls to services, e.g. ``light.turn_on``.
	**Type**: str
	/ **Default**: "brightness"

on_service
  The name of the service to be called for turning an entity on. Note that the dot separating component and service must be replaced by a forward slash (``/``)
	**Type**: str
	/ **Default**: "light/turn_on"

off_service
  The name of the service to be called for turning an entity off. Note that the dot separating component and service must be replaced by a forward slash (``/``)
	**Type**: str
	/ **Default**: "light/turn_off"

toggle_service
  The name of the service to be called for toggling an entity. Note that the dot separating component and service must be replaced by a forward slash (``/``)
	**Type**: str
	/ **Default**: "light/toggle"

ignore_off
  Setting this to ``true`` causes switched-off entities to be ignored during dimming (instead of turning them on). This allows to control multiple different lighting scenes with a single Goetterdimmerung instance. See the :ref:`M̀ultiple Scenes Example <example_multiple_scenes>`.
	**Type**: bool
	/ **Default**: false
	
.. _config_steps:

steps
  The number of dimming steps. Note that this can be different from the number of values that are possible for the controlled value ("brightness") of the entities.
	**Type**: int
	/ **Default**: 255

.. _config_increment:

increment
  The number of :ref:`steps <config_steps>` to increase / decrease the internal step counter at every :ref:`interval <config_interval>`.
	**Type**: int
	/ **Default**: 20

.. _config_interval:

interval_ms
  The interval in miliseconds between two dimming :ref:`steps <config_steps>`
	**Type**: int
	/ **Default**: 200

start_up
  The event at which to start dimming up. See the :ref:`event specification documentation <conf_event>` for details.
	**Type**: :ref:`event specification <conf_event>`

stop_up
  The event at which to stop dimming up. See the :ref:`event specification documentation <conf_event>` for details.
	**Type**: :ref:`event specification <conf_event>`

start_down
  The event at which to start dimming down. See the :ref:`event specification documentation <conf_event>` for details.
	**Type**: :ref:`event specification <conf_event>`

stop_down
  The event at which to stop dimming down. See the :ref:`event specification documentation <conf_event>` for details.
	**Type**: :ref:`event specification <conf_event>`

on_event
  The event at which to turn all entities on. See the :ref:`event specification documentation <conf_event>` for details.
	**Type**: :ref:`event specification <conf_event>`

off_event
  The event at which to turn all entities off. See the :ref:`event specification documentation <conf_event>` for details.
	**Type**: :ref:`event specification <conf_event>`

toggle_event
  The event at which to toggle all entities. See the :ref:`event specification documentation <conf_event>` for details.
	**Type**: :ref:`event specification <conf_event>`
	

.. _conf_entity:

Entity Configuration
--------------------

The ``entities`` key of the global configuration expects a list of entities. An example of such a list could be:

.. code-block: yaml

	my_dimmer:
		[…]
		entities:
			- entity_id: light.some_light
				min: 10
				max: 255
			- entity_id: light.other_light
				start: 100

Each element of the list denotes one controlled entity. Each entity has the following configuration options:

entity_id
  The entity ID of the controlled entity.
	**Type**: Entity ID (str)

min
  Minimum value ("brightness") to ever send to the entity. The light will never be dimmed below this value (unless turned off).
	**Type**: int
	/ **Default**: 0

max
  Maximum value ("brightness") to ever send to this entity. The light will never be dimmed above this value.
	**Type**: int
	/ **Default**: 255

start
  The minimum :ref:`step <config_steps>` at which this light should be turned on. At steps below this step, the light will be turned off.
	**Type**: int
	/ **Default**: 0

end
  The :ref:`step <config_steps>` at which this light should reach its maximum brightness. All steps above this step will still only set the light to its maximum brightness.
	**Type**: int
	/ **Default**: The maximum number of :ref:`steps <config_steps>`

weight
  The weight of this light. When two lights are dimmed up simultaneously, their brightness should increase proportionally to their weight.
	**Type**: float
	/ **Default**: 1.0

initial
  Specification of how to get attributes for this entity when turning it on. See the :ref:`initial values config <conf_initial>` for details. This allows to always turn lights on with a specified brightness, or color, or white temperature.
	**Type**: :ref:`initial value config <conf_initial>`

off_state
  The state that should be considered ``off`` for this device.
	**Type**: str
	/ **Default**: "off"

.. _conf_initial:

Initial Value Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``initial`` option in the entity configuration allows to retrieve arbitrary attributes to be sent with the ``turn_on`` service calls. The configuration is a dictionary, where every key corresponds to an attribute to be sent. For each of these attributes, there are three ways of configuring a value:

* A string that does not contain a dot is treated as a fixed value
* A string that contains a dot is treated as an entity ID. The respective entity's state is used as value.
* A dictionary must contain an ``entity_id`` or a ``value`` and a ``type``. The entity's state (resp. the fixed value) is cast into the requested type.

These are examples of setting the ``color_temperature`` attribute for a light:

Setting a fixed value of 100::

  initial:
	  color_temperature: 100

Setting a fixed value of 100, casting to int::

  initial:
	  color_temperature:
	    value: 100
		  type: "int"

Getting the state of an ``input_number``, casting to int::
	
	initial:
	  color_temperature:
		  entity_id: input_number.some_entity
			type: "int
	

.. _conf_event:

Event Specification
===================

Several configuration options allow for the specification of an event. Every event specification is a dictionary. It must have a key ``event`` specifying the type of event to listen for. Additionally, it may have a key ``event_data``, which can in turn contain a dictionary of arbitrary key-value mappings. The respective function will only be triggered if every key-value mapping in the ``event_data`` dictionary is also present in the event data of the fired event.

This configuration starts the "dim up" function only if a ``deconz_event`` of type ``1002`` was fired from a button with the id ``my_button``::
	
	dim_up_start:
	  event: "deconz_event"
		event_data:
		  id: "my_button"
			event: 1002
