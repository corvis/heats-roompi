from random import random

from typing import Dict

from common.errors import InvalidModuleError
from common.model import StateAwareModule, ParameterDef, Driver


class OneWireThermometerModule(StateAwareModule):
    @staticmethod
    def typeid() -> int:
        return 0x0103

    @staticmethod
    def type_name() -> str:
        return '1wireThermometer'

    def __init__(self, application, drivers: Dict[int, Driver]):
        super().__init__(application, drivers)
        self.device_id = None  # type: str
        self.__update_interval = self.MINIMAL_ITERATION_INTERVAL

    def step(self):
        self.logger.info("Iteration: " + self.name)
        self.state.temperature = int(random() * 1000)
        self.commit_state()

    @property
    def update_interval(self):
        return self.MINIMAL_ITERATION_INTERVAL

    @update_interval.setter
    def update_interval(self, value:[str,int]):
        if isinstance(value, int):
            self.MINIMAL_ITERATION_INTERVAL = value
        else:
            raise InvalidModuleError("OneWireThermometerModule: update_interval should be "
                                     "integer value representing time in millis")

    STATE_FIELDS = ['temperature']
    ACTIONS = []
    PARAMS = [
        ParameterDef('device_id', is_required=True),
        ParameterDef('update_interval', is_required=False),
    ]
    MINIMAL_ITERATION_INTERVAL = 10 * 1000
    REQUIRED_DRIVERS = []
