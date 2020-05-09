.. Goetterdimmerung documentation master file, created by
   sphinx-quickstart on Thu May  7 20:15:06 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Goetterdimmerung's documentation!
============================================

Goetterdimmerung is an App for `Home Assistant <https://www.home-assistant.io/>`_'s `AppDaemon 4 <https://appdaemon.readthedocs.io/en/latest/>`_. It can be used to smoothly increase ("dim up") or decrease ("dim down") settings in Home Assistant, using simple buttons or switches as control elements. While it is mainly intended to control the brightness of lights, it can also be used to control for example a fan speed, a thermostat temperature or many more values.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
  
   configuration
   examples


Getting Started
---------------

We'll assume that you have Home Assistant and AppDaemon already set up. If not, have a look at their respective documentations on how to install them. Copy Goetterdimmerung's folder into your AppDaemon's ``apps`` folder (that's the one containing ``apps.yaml``). Or, if you want to easily upgrade, you can just ``git clone`` the whole project into a folder in the ``apps`` folder.

After a restart of AppDaemon, all that's left to do is to configure your Goetterdimmerung instances. Here is a simple example that just uses a switch with two buttons, which send different events when they are pressed / held / released, respectively (to be exact - an Ikea Trådfri dimmer via Home Assistant's Deconz integration):

.. code-block:: yaml

   my_dimmer:
     module: goetterdimmerung
     class: Goetterdimmerung
     entities:
       - entity_id: light.some_light
     off_event:
       event: deconz_event
       event_data:
         id: "my_switch"
         event: 2002
     on_event:
       event: deconz_event
       event_data:
         id: "my_switch"
         event: 1002
     start_up:
       event: deconz_event
       event_data:
         id: "my_switch"
         event: 1001
     stop_up:
       event: deconz_event
       event_data:
         id: "my_switch"
         event: 1003
     start_down:
       event: deconz_event
       event_data:
         id: "my_switch"
         event: 2001
     stop_down:
       event: deconz_event
       event_data:
         id: "my_switch"
         event: 2003

				 
For details, have a look at the config documentation.
             

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
