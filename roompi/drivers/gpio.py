import logging
from abc import abstractmethod

from roompi.controller.device import Driver

GPIO_IN = 0
GPIO_OUT = 1


class GPIODriver(Driver):
    def __init__(self):
        super(GPIODriver, self).__init__()

    @abstractmethod
    def setup(self, pin, mode):
        """
        Setup operation mode for the given pin.
        :param pin: pin identifier
        :param mode: mode to be set for the given pin. It might be whether GPIO_IN or GPIO_OUT
        :return:
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Dispose all system resources related to the GPIO subsystem and resets GPIO state
        :return:
        """
        pass

    @abstractmethod
    def read(self, pin):
        """
        Returns the state of the pin
        :param pin:
        :return: state of the pin. It might be 0 or 1
        :rtype: int
        """
        pass

    @abstractmethod
    def set(self, pin, state):
        """
        Set the state for the given pin. Note pin should be configured
        :param pin: pin to be modified
        :param state: state to be set. 0 or 1
        :type: int
        :return:
        """
        pass


class FakeGPIODriver(GPIODriver):

    def __init__(self):
        super(FakeGPIODriver, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def on_loaded(self, application_context):
        self.logger.info("Loaded FakeGPIO driver")

    def get_interface(self):
        return GPIODriver

    def setup(self, pin, mode):
        """
        Setup operation mode for the given pin.
        :param pin: pin identifier
        :param mode: mode to be set for the given pin. It might be whether GPIO_IN or GPIO_OUT
        :return:
        """
        pass

    def cleanup(self):
        """
        Dispose all system resources related to the GPIO subsystem and resets GPIO state
        :return:
        """
        pass

    def read(self, pin):
        """
        Returns the state of the pin
        :param pin:
        :return: state of the pin. It might be 0 or 1
        :rtype: int
        """
        return 0

    def set(self, pin, state):
        """
        Set the state for the given pin. Note pin should be configured
        :param pin: pin to be modified
        :param state: state to be set. 0 or 1
        :type: int
        :return:
        """
        self.logger.info("FakeGPIO: set pin {}: {}".format(pin, state))