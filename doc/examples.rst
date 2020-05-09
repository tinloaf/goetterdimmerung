Example Configurations
======================

.. _file_examples:

Simple Example
--------------

In this example, there is just one entity (``light.some_light``) that should be dimmed up/down by an Ikea Trådfri dimmer connected via the Deconz integration. These dimmers send events of type ``1001`` if the 'up' button was pressed and held, and of type ``1003`` if the 'up' button was released. If the 'up' button was only pressed shortly (which we will use to turn the light on), ``1002`` is sent. For the 'down' button, the respective events are ``2001``, ``2003`` and ``2002``. The name of the button is ``my_button``.

We never want the light to be turned off by just dimming down, so we set a minimum value of ``10``.

.. code-block:: yaml
                
   my_app:
     module: goetterdimmerung
     class: goetterdimmerung

     entities:
       - entity_id: light.some_light
         min: 10

     off_event:
       event: deconz_event
       event_data:
         id: "my_button"
         event: 2002
     on_event:
       event: deconz_event
       event_data:
         id: "my_button"
         event: 1002
     start_up:
       event: deconz_event
       event_data:
         id: "my_button"
         event: 1001
     stop_up:
       event: deconz_event
       event_data:
         id: "my_button"
         event: 1003
     start_down:
       event: deconz_event
       event_data:
         id: "my_button"
         event: 2001
     stop_down:
       event: deconz_event
       event_data:
         id: "my_button"
         event: 2003

.. _example_multiple_scenes:		

Multiple Scenes With One Dimmer
-------------------------------

In this example, we still only have the one dimmer from above, but we now have three lights: ``light.light_a``, ``light.light_b`` and ``light.light_c``. We want to have two scenes, one where lights ``a`` and ``b`` are on, and one where ``b`` and ``c`` are on. Both these scenes should be toggled by short-pressing the upper/lower button on the dimmer. Holding the dimmer buttons should dim up/down whatever is currently active.

We achieve this by having three instances of ``Goetterdimmerung``: Two to toggle the respective scenes (we could of course also do that directly in Home Assistant, without ``Goetterdimmerung``), one that dims whatever is currently active. The key here is to use the ``ignore_off`` option.

.. code-block:: yaml
                
   toggle_a:
     module: goetterdimmerung
     class: goetterdimmerung

     entities:
       - entity_id: light.light_a
         min: 10
       - entity_id: light.light_b
         min: 10

     toggle_event:
       event: deconz_event
       event_data:
         id: "my_button"
         event: 1002

   toggle_b:
     module: goetterdimmerung
     class: goetterdimmerung

     entities:
       - entity_id: light.light_b
         min: 10
       - entity_id: light.light_c
         min: 10

     toggle_event:
       event: deconz_event
       event_data:
         id: "my_button"
         event: 2002

    dimmer:
      module: goetterdimmerung
      class: Goetterdimmerung

      entities:
        - entity_id: light.light_a
          min: 10
        - entity_id: light.light_b
          min: 10
        - entity_id: light.light_c
          min: 10

      ignore_off: true
      
      start_up:
        event: deconz_event
        event_data:
          id: "my_button"
          event: 1001
      stop_up:
        event: deconz_event
        event_data:
          id: "my_button"
          event: 1003
      start_down:
        event: deconz_event
        event_data:
          id: "my_button"
          event: 2001
      stop_down:
        event: deconz_event
        event_data:
          id: "my_button"
          event: 2003

          
