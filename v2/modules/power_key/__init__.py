import logging

from common.model import Module, EventDef, ActionDef, ParameterDef

ACTION_OFF = 0x01
ACTION_ON = 0x02
ACTION_TOGGLE = 0x03

EVENT_STATE_CHANGED = 0x01


class PowerKeyModule(Module):

    def __init__(self, application):
        super().__init__(application)
        self.__logger = logging.getLogger('PowerKeyModule')
        self.gpio = 0

    def off(self):
        pass

    def on(self):
        pass

    def toggle(self):
        pass

    def set_state(self, state):
        # TODO: logic here
        self.emit(EVENT_STATE_CHANGED, state)

    @staticmethod
    def typeid() -> int:
        return 0x0100

    @staticmethod
    def type_name() -> str:
        return 'PowerKey'

    def step(self):
        self.__logger.info("Iteration")

    ACTIONS = [
        ActionDef(ACTION_OFF, 'off', off),
        ActionDef(ACTION_ON, 'on', on),
        ActionDef(ACTION_TOGGLE, 'toggle', toggle)
    ]
    EVENTS = [
        EventDef(EVENT_STATE_CHANGED, 'changed')
    ]
    PARAMS = [
        ParameterDef('gpio', is_required=True),
    ]
    MINIMAL_ITERATION_INTERVAL = 2 * 1000
