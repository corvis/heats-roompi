import logging

from typing import List, Dict

from common.drivers import GPIODriver
from common.model import Module, EventDef, ActionDef, ParameterDef, StateAwareModule, Driver

ACTION_OFF = 0x01
ACTION_ON = 0x02
ACTION_TOGGLE = 0x03


class PowerKeyModule(StateAwareModule):
    STATE_FIELDS = ['is_on']

    def __init__(self, application, drivers: Dict[int, Driver]):
        super().__init__(application, drivers)
        self.__logger = logging.getLogger('PowerKeyModule')
        self.gpio = 0

    @staticmethod
    def typeid() -> int:
        return 0x0100

    @staticmethod
    def type_name() -> str:
        return 'PowerKey'

    def off(self, **kwargs):
        self.set_state(False)

    def on(self, **kwargs):
        self.set_state(False)

    def toggle(self, **kwargs):
        self.set_state(not self.is_on)

    def set_state(self, state):
        self.is_on = state in [1, True, '1', 'true', 'on']

    def step(self):
        self.__logger.info("Iteration")

    @property
    def is_on(self) -> bool:
        return self.state.is_on

    @is_on.setter
    def is_on(self, val: bool):
        # TODO: Call driver
        self.state.is_on = val
        self.commit_state()

    ACTIONS = [
        ActionDef(ACTION_OFF, 'off', off),
        ActionDef(ACTION_ON, 'on', on),
        ActionDef(ACTION_TOGGLE, 'toggle', toggle)
    ]

    PARAMS = [
        ParameterDef('gpio', is_required=True),
    ]
    MINIMAL_ITERATION_INTERVAL = 2 * 1000
    REQUIRED_DRIVERS = [GPIODriver.typeid()]
