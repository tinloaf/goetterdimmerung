import sys
import hassapi as hass
import asyncio
from bisect import bisect_left


class Entities(object):
    """Class that holds the list of entities managed by an instance of
    Goetterdimmerung.  Also responsible for computing the mapping of
    steps to actual values sent to the respective entities.
    """
    class Entity(object):
        """ A single managed entity"""

        def __init__(self, eid, emin, emax, start, end, weight, initial_vals,
                     off_state):
            """Create an entity.

            Parameters
            ----------
            eid : str
                  Entity ID of the managed entity.
            emin : int
                   Minimum value to dim this entity to
            emax : int
                   Maximum value to dim this entity to
            start : int
                    Step at which this entity should start dimming up
            end : int
                  Step at which this entity should have maximum brightness
            weight : float
                     Weight of the entity. Entities' dimming speed will be
                     proportional to their weight.
            initial_vals : dict
                           Specification of how to get initial values when
                           turning on the entity.
            off_state : str
                        Specification of which state should be considered "off"
            """
            self.eid = eid
            self.emin = emin
            self.emax = emax
            self.start = start
            self.end = end
            self.weight = weight
            self.initial_vals = initial_vals
            self.off_state = off_state

    def __init__(self, data, plugin, default_end):
        self._data = data
        self._plugin = plugin
        self._default_end = default_end
        self._entities = {}

        self._break_points = []
        self._segment_factors = []
        self._segment_offsets = []
        self._steps_to_entity = {}

        self._last_index = 0

        self._plugin.log("Parsing entities")
        self._parse_entities()
        self._plugin.log("Creating segments")
        self._create_segments()
        self._plugin.log("Entities initialized")

    def get_eids(self):
        """Return all managed entities' IDs"""
        return self._entities.keys()

    def get_entity(self, eid):
        """Return the Entity object with the specified entity ID"""
        return self._entities[eid]

    def get_all_at(self, step, eids):
        """Return the value of all entities in eids at a specified step.

        Parameters
        ----------
        step : int
               The step which to report the values for
        eids : list of str
               List of entity IDs corresponding to the list of entities for
               which to get the values

        Returns
        -------
        iterable of ( entity_id, value )

        """
        while self._break_points[self._last_index] > step:
            self._last_index -= 1

        while self._break_points[self._last_index + 1] < step:
            self._last_index += 1

        return ((self._entities[eid],
                 self._get_at_current_step(eid, step)) for eid in eids)

    def _get_at_current_step(self, eid, step):
        return self._entities[eid].emin \
            + self._segment_offsets[self._last_index][eid] \
            + (step - self._break_points[self._last_index]) \
            * self._segment_factors[self._last_index][eid] \
            * self._steps_to_entity[eid]

    def _create_segments(self):
        points = set()
        for entity in self._entities.values():
            points.add(entity.start)
            points.add(entity.end)

        self._break_points = list(points)
        assert(len(self._break_points) >= 2)

        total_weight = [0] * (len(self._break_points) - 1)
        for entity in self._entities.values():
            point = bisect_left(self._break_points, entity.start)
            assert(self._break_points[point] == entity.start)
            while self._break_points[point] < entity.end:
                total_weight[point] += entity.weight
                point += 1

        weighted_steps = {eid: 0.0 for eid in self._entities.keys()}

        for i in range(0, len(self._break_points) - 1):
            self._segment_factors.append({})
            self._segment_offsets.append({})
            for (eid, entity) in self._entities.items():
                w = entity.weight / total_weight[i]
                self._segment_factors[i][eid] = w
                self._segment_offsets[i][eid] = weighted_steps[eid]
                weighted_steps[eid] += (self._break_points[i + 1] -
                                        self._break_points[i]) * w

        for (eid, entity) in self._entities.items():
            self._steps_to_entity[eid] = (
                entity.emax - entity.emin) / weighted_steps[eid]

    def _parse_entities(self):
        for entity in self._data:
            self._entities[entity['entity_id']] = Entities.Entity(
                entity['entity_id'],
                entity.get('min', 0),
                entity.get('max', 255),
                entity.get('start', 0),
                entity.get('end', self._default_end),
                entity.get('weight', 1.0),
                entity.get('initial', {}),
                entity.get('off_state', 'off'))


class Goetterdimmerung(hass.Hass):
    """Goetterdimmerung entity dimmer"""
    async def initialize(self):
        self._steps = self.args.get('steps', 255)
        self._entities = Entities(self.args['entities'], self, self._steps)

        self._attribute = self.args.get('attribute', 'brightness')
        self._on_service = self.args.get('on_service', 'light/turn_on')
        self._off_service = self.args.get('off_service', 'light/turn_off')
        self._toggle_service = self.args.get('toggle_service', 'light/toggle')

        self._ignore_off = self.args.get('ignore_off', False)

        # TODO condition must be checked!
        if 'condition' in self.args:
            self._condition = self.args['condition']
        else:
            self._condition = None

        #
        # State tracking of managed apps
        #
        # Set to true to temporarily ignore new values. Useful during dimming,
        # since changes may occurr rapidly and out of order
        self._ignore_states = False
        self._states = {}

        await self._initialize_tracking()

        self._step = None
        self._increment = self.args.get('increment', 20)
        self._interval = self.args.get('interval_ms', 200)

        self._loop = asyncio.get_event_loop()

        await self._start_listening()

        self._current_increment = None
        self._current_interval = None

    def _get_filtered_eids(self):
        return [eid for eid in self._entities.get_eids()
                if self._states[eid] != (self._entities
                                         .get_entity(eid).off_state)]

    async def _state_cb(self, eid, attr, old, new, kwargs):
        if attr != self._attribute:
            return

        if self._ignore_states:
            return

        self._states[eid] = new
        self._step = None
        # TODO inflight tracking

    async def _refresh_state_cache(self):
        for eid in self._entities.get_eids():
            self._states[eid] = await self.get_state(entity_id=eid,
                                                     attribute=self._attribute)

    async def _initialize_tracking(self):
        # First, register tracking callbacks for all managed entities
        for eid in self._entities.get_eids():
            self.listen_state(self._state_cb, eid, attribute=self._attribute)

        # Now, initialize states
        await self._refresh_state_cache()

    # TODO this is a very rudimentary least-squares fitter
    async def _invert_step(self):
        values = {}

        def cost(values, step):
            computed_vals = self._entities.get_all_at(
                step, self._get_filtered_eids())
            cost = 0.0
            for (entity, val) in computed_vals:
                if entity.eid not in values:
                    continue
                cost += (values[entity.eid] - val)**2

            return cost

        for eid in self._get_filtered_eids():
            try:
                val = float(self._states[eid])
                values[eid] = val
            except TypeError:
                # off or other error. If we have turn-on default values for
                # this entity, use that. Else, ignore this entity
                initial_vals = await self._get_initial_vals(
                    self._entities.get_entity(eid))
                if self._attribute in initial_vals:
                    values[eid] = float(initial_vals)

        best_cost = cost(values, 0)
        best_step = 0
        l = 0
        h = self._steps

        while h > (l + 1):
            m = int((h + l) / 2)

            cost_at_m = cost(values, m)

            if m > 0:
                cost_below = cost(values, m-1)
            else:
                cost_below = sys.float_info.max

            if m < h:
                cost_above = cost(values, m+1)
            else:
                cost_above = sys.float_info.max

            if cost_at_m < best_cost:
                best_cost = cost_at_m
                best_step = m
            if cost_below < best_cost:
                best_cost = cost_below
                best_step = m-1
            if cost_above < best_cost:
                best_cost = cost_above
                best_step = m+1

            if cost_below < cost_above:
                h = m
            else:
                l = m

        return best_step

    async def _check_condition(self):
        if not self._condition:
            return True

        state = await self.get_state(entity_id=self._condition['entity'])
        return str(state).lower() == str(self._condition['state']).lower()

    async def _change(self):
        if not self._step:
            step = await self._invert_step()
        else:
            step = self._step

        # Ignore incoming state changes. They are caused by ourselves and
        # would mess up step caching
        self._ignore_states = True
        while (self._current_increment is not None and
               self._current_interval is not None):
            step += self._current_increment
            step = max(0, min(self._steps, step))
            self._step = step

            futures = []
            for (entity, val) in self._entities.get_all_at(
                    step, self._get_filtered_eids()):
                service_args = {'entity_id': entity.eid,
                                self._attribute: int(val)}
                futures.append(self.call_service(
                    service=self._on_service, **service_args))

            await asyncio.gather(*futures)
            if self._current_interval:  # Dimming has stopped
                await self.sleep(self._current_interval / 1000)

            if step == self._steps and \
               self._current_increment and self._current_increment > 0:
                # stop the dim-up
                self._current_increment = None
                self._current_interval = None
            if step == 0 and \
               self._current_increment and self._current_increment < 0:
                # stop the dim-down
                self._current_increment = None
                self._current_interval = None

        # Update state cache and re-enable state tracking - after a
        # brief pause to allow for in-flight changes to settle
        await self.sleep(200)
        self._ignore_states = False
        await self._refresh_state_cache()

    async def _start_up(self, event_name, data, kwargs):
        if not await self._check_condition():
            return

        self._current_increment = self._increment
        self._current_interval = self._interval
        await self._change()

    async def _stop_up(self, event_name, data, kwargs):
        self._current_increment = None
        self._current_interval = None

    async def _start_down(self, event_name, data, kwargs):
        if not await self._check_condition():
            return

        self._current_increment = -1 * self._increment
        self._current_interval = self._interval
        await self._change()

    async def _stop_down(self, event_name, data, kwargs):
        self._current_increment = None
        self._current_interval = None

    async def _get_initial_vals(self, entity):
        data = {}
        for (k, v) in entity.initial_vals.items():
            if isinstance(v, str) and v.find('.') != -1:
                # This is treated as an entity id. Get its state as
                # initial value
                data[k] = str(await self.get_state(v))
            elif isinstance(v, dict):
                if 'entity_id' in v:
                    raw = await self.get_state(v['entity_id'])
                elif 'value' in v:
                    raw = v['value']
                else:
                    self.log(('ERROR: No way to retrieve an initial value'
                              ' for attr {} of entity {}').format(
                                  k, entity.eid))

                # TODO have a hardcoded list of defaults
                t = v.get('type', 'str')
                if t == 'int':
                    raw = int(float(raw))
                if t == 'float':
                    raw = float(raw)
                if t == 'str':
                    raw = str(raw)
                data[k] = raw
            else:
                data[k] = v
        return data

    async def _turn_on(self, event_name, data, kwargs):
        tasks = []
        for eid in self._entities.get_eids():
            service_args = await self._get_initial_vals(
                self._entities.get_entity(eid))
            service_args['entity_id'] = eid

            tasks.append(self.call_service(
                service=self._on_service, **service_args))
        await asyncio.gather(*tasks)

    async def _turn_off(self, event_name, data, kwargs):
        tasks = []
        for eid in self._entities.get_eids():
            service_args = {'entity_id': eid}
            tasks.append(self.call_service(
                service=self._off_service, **service_args))
        await asyncio.gather(*tasks)

    async def _toggle(self, event_name, data, kwargs):
        tasks = []
        for eid in self._entities.get_eids():
            service_args = await self._get_initial_vals(
                self._entities.get_entity(eid))
            service_args['entity_id'] = eid

            tasks.append(self.call_service(
                service=self._toggle_service, **service_args))
        await asyncio.gather(*tasks)

    async def _cb_wrapper(self, event_name, data, kwargs):
        if str(data['event']) != str(kwargs['inner_event']):
            return

        cb = getattr(self, kwargs['inner_cb_name'])
        await cb(event_name, data, kwargs)

    async def _start_listening(self):
        self._start_up_event = self.args['start_up']
        self._stop_up_event = self.args['stop_up']
        self._start_down_event = self.args['start_down']
        self._stop_down_event = self.args['stop_down']

        events = [(self._start_up, self.args['start_up']),
                  (self._start_down, self.args['start_down']),
                  (self._stop_up, self.args['stop_up']),
                  (self._stop_down, self.args['stop_down'])]

        if 'on_event' in self.args:
            events.append((self._turn_on, self.args['on_event']))

        if 'off_event' in self.args:
            events.append((self._turn_off, self.args['off_event']))

        if 'toggle_event' in self.args:
            events.append((self._turn_off, self.args['toggle_event']))

        for (cb, event) in events:
            if 'event' in event.get('event_data', {}):
                # Clashes with listen_event's kw args
                ev_data = dict(event['event_data'])
                ev_data['inner_cb_name'] = cb.__name__
                ev_data['inner_event'] = ev_data['event']
                del ev_data['event']

                self.listen_event(self._cb_wrapper, event['event'], **ev_data)
            else:
                self.listen_event(
                    cb, event['event'], **event.get('event_data', {}))
