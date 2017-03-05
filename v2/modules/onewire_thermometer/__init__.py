from random import random

from typing import Dict

from common.model import StateAwareModule, ActionDef, ParameterDef, Driver


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

    def step(self):
        self.state.temperature = int(random() * 1000)
        self.commit_state()

    STATE_FIELDS = ['temperature']
    ACTIONS = []
    PARAMS = [
        ParameterDef('device_id', is_required=True),
    ]
    MINIMAL_ITERATION_INTERVAL = 2 * 1000
    REQUIRED_DRIVERS = []
