import logging
from common.drivers import GPIODriver


class FakeGPIODriver(GPIODriver):

    def __init__(self):
        self.__logger = logging.getLogger('FakeGPIODriver')

    def read(self, pin: int) -> int:
        return 0

    def set(self, pin: int, state: int):
        self.__logger.info("Set pin {}: {}".format(pin, state))
