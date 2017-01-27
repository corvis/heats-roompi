import logging

import time

from common import utils
from .utils import int_to_hex4str
from .errors import InvalidModuleError, InvalidDriverError
from .model import InstanceSettings, Driver, Module


class ModuleRegistry:
    def __init__(self):
        super().__init__()
        self.modules = {}

    def find_module_by_name(self, module_name):
        for x in self.modules.values():
            if x.type_name() == module_name:
                return x
        raise InvalidModuleError('Unknown module {} '.format(module_name))

    def register(self, module_class):
        module_class_name = module_class.__name__
        try:
            # Validations
            if not issubclass(module_class, Module):
                raise InvalidModuleError("Module should implement Module class")
            typeid = module_class.typeid()
            if typeid < 0:
                raise InvalidModuleError('Incorrect module type')
            if typeid in self.modules.keys():
                raise InvalidModuleError(
                    'Module {} is already registered'.format(int_to_hex4str(typeid), module_class.type_name()))
            self.modules[typeid] = module_class
        except InvalidModuleError as e:
            raise InvalidModuleError("Can't register module " + module_class_name + ": " + e.message, e)

    def create_module_instance(self, application, typeid: int, instance_id: int, instance_name: str) -> Module:
        try:
            if typeid not in self.modules:
                raise InvalidModuleError("Unknown module type:".format(typeid))
            instance = self.modules.get(typeid)(application)
            instance.id = instance_id
            instance.name = instance_name
            # Parameters and validation
            # TODO:
            return instance
        except InvalidModuleError as e:
            raise InvalidModuleError("Unable to create module for device {}: {}".format(instance_id, e.message), e)


class ApplicationManager:
    def __init__(self):
        self.__instance_settings = InstanceSettings()
        self.drivers = {}
        self.devices = {}
        self.__logger = logging.getLogger('ApplicationManager')
        self.__main_loop = []
        self.__module_registry = ModuleRegistry()
        self.__terminating = False

    def get_instance_settings(self) -> InstanceSettings:
        return self.__instance_settings

    def get_module_registry(self) -> ModuleRegistry:
        return self.__module_registry

    def get_driver(self, driver_type: int) -> Driver:
        driver_impl = self.drivers.get(driver_type, None)
        if driver_impl is None:
            raise InvalidDriverError(
                'There is not implementation for driver {} registered'.format(int_to_hex4str(driver_type)))
        return driver_impl

    def register_driver(self, driver_class_name):
        try:
            if isinstance(driver_class_name, str):
                # Load driver
                try:
                    module_name, class_name = driver_class_name.rsplit('.', 1)
                    module = __import__(module_name, globals(), locals(), [class_name], 0)
                    driver_impl_class = getattr(module, class_name)
                except ImportError as e:
                    raise InvalidDriverError("Class doesn't exist", e)
            else:
                driver_impl_class = driver_class_name
            # Validations
            if not issubclass(driver_impl_class, Driver):
                raise InvalidDriverError('Driver should implement common.model.Driver class')
            typeid = driver_impl_class.typeid()
            if typeid < 0:
                raise InvalidDriverError('Incorrect driver type')
            if typeid in self.drivers.keys():
                raise InvalidDriverError(
                    'Driver implementation for is already registered'.format(driver_impl_class.type_name()))
            # Initialization
            driver_impl = driver_impl_class()
            try:
                driver_impl.on_initialized(self)
            except Exception as e:
                raise InvalidDriverError("Error during initialization", e)
            self.drivers[typeid] = driver_impl
            self.__logger.info('Loaded driver {}({} driver): '.format(int_to_hex4str(driver_impl.typeid()),
                                                                      driver_impl.type_name()) + driver_impl.__class__.__name__)
        except InvalidDriverError as e:
            raise InvalidDriverError('Unable to register driver {}: '.format(driver_class_name) + e.message, e)

    def register_device(self, device: Module):
        self.devices[device.id] = device
        if device.IN_LOOP:
            self.__main_loop.append(device)

    def main_loop(self):
        while not self.__terminating:
            for device in self.__main_loop:
                if device.last_step > 0 and utils.delta_time(device.last_step) < device.MINIMAL_ITERATION_INTERVAL:
                    continue
                try:
                    device.step()
                    device.last_step = utils.capture_time()
                except Exception as e:
                    self.__logger.error("Error in during main loop execution: " + str(e))
            time.sleep(0.001)

    def shutdown(self):
        self.__logger.info("Initiating shutdown process")
        self.__terminating = True
        for device in self.devices.values():
            try:
                device.on_before_destroyed()
            except Exception as e:
                self.__logger.error(
                    "Error while destroying device {}({}): {}".format(int_to_hex4str(device.id), device.name, e))
        self.__logger.info("Deactivated devices")
        for driver in self.drivers.values():
            try:
                driver.on_before_unloaded(self)
            except Exception as e:
                self.__logger.error(
                    "Error while destroying driver {}({}): {}".format(int_to_hex4str(driver.typeid()), driver.type_name(), e))
        self.__logger.info("Unloaded drivers")