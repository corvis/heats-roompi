from .model import Driver


class GPIODriver(Driver):
    GPIO_IN = 0
    GPIO_OUT = 1

    @staticmethod
    def typeid() -> int:
        return 0x1001

    @staticmethod
    def type_name() -> str:
        return 'GPIO'

    def cleanup(self):
        """
        Dispose all system resources related to the GPIO subsystem and resets GPIO state
        """
        pass

    def read(self, pin: int) -> int:
        """
        Returns the state of the pin
        :param pin:
        :return: state of the pin. It might be 0 or 1
        :rtype: int
        """
        pass

    def set(self, pin: int, state: int):
        """
        Set the state for the given pin. Note pin should be configured
        :param pin: pin to be modified
        :param state: state to be set. 0 or 1
        :type: int
        :return:
        """
        pass


class ModuleDiscoveryDriver(Driver):

    @staticmethod
    def typeid() -> int:
        return 0x1002

    @staticmethod
    def type_name() -> str:
        return 'ModuleDiscovery'

    def discover_modules(self, module_registry):
        pass