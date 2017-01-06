import logging
from abc import ABCMeta, abstractmethod
from threading import Thread
import threading
from time import sleep
from roompi.modules import registry, ModuleInitializationError
from roompi.modules.errors import ContextInitializationError

try:
    import RPi.GPIO as GPIO
except:
    import roompi.mock.GPIO as GPIO

__author__ = 'LOGICIFY\corvis'


class ApplicationContext(dict):
    def register_singleton(self, instance):
        if instance is None:
            raise ValueError("Unable to register singleton instance in application context: Can't be None")
        self[instance.__class__.__name__] = instance

    def register_driver(self, driver_instance):
        if not isinstance(driver_instance, Driver):
            raise ContextInitializationError("Unable to register driver instance {} since it "
                                             "is not implementing Driver".format(driver_instance))
        interface = driver_instance.get_interface()
        if interface is not None:
            self[interface] = driver_instance
        self[driver_instance.get_interface_name()] = driver_instance

    def get_driver(self, interface_or_interface_name):
        """
        Returns driver which implements given interface
        :param interface_or_interface_name:
        :rtype: Driver
        """
        return self.get(interface_or_interface_name)

    @property
    def application_settings(self):
        """
        :rtype: roompi.controller.device.InstanceSettings
        """
        return self.get('InstanceSettings')

    @property
    def device_controller(self):
        """
        :rtype: roompi.controller.device.DeviceController
        """
        return self.get('DeviceController')


class Driver(metaclass=ABCMeta):
    """
    Base abstract class for all application services
    """

    def __init__(self):
        super(Driver, self).__init__()

    @abstractmethod
    def on_loaded(self, application_context):
        """
        Method which will be invoked once service loaded
        :type application_context: ApplicationContext
        :return:
        """
        pass

    def get_interface_name(self):
        """
        Returns name of the interface this service is implementing
        :return:
        """
        return self.get_interface().__name__

    @abstractmethod
    def get_interface(self):
        return self


class InstanceSettings:
    """
    Represents instance configuration
    """

    def __init__(self, config=None):
        if config is None:
            config = {}
        self.instance_config = config

    def get(self, option, default=None):
        return self.instance_config.get(option, default)

    @property
    def instance_id(self):
        return self.instance_config.get("id", "default")


class DeviceController(object):
    @staticmethod
    def __parse_link_string(str):
        """
        Returns tuple: (device_id, action). If action is not set - returns (device_id, None)
        """
        if '.' in str:
            device_id, action = str.split('.')
        else:
            device_id, action = str, None
        if device_id.startswith('#'):
            device_id = device_id.replace('#', '')
        return device_id, action

    def __init__(self, devices_config_section, application_context):
        self.application_context = application_context
        self.application_context.register_singleton(self)
        registry.autodiscover()
        self.devices = {}
        self.managed_threads = []
        self.logger = logging.getLogger('DeviceController')
        self.step_interval = 50
        for device_id, device_conf in devices_config_section.items():
            device_conf['id'] = device_id
            self.devices[device_id] = registry.create_module(device_conf, self.application_context)
        # The second cycle should create pipes between devices
        for device_id, device_conf in devices_config_section.items():
            device = self.devices[device_id]
            pipe_data = device_conf.get('pipe')
            if pipe_data is not None:
                for event_name, link_data in pipe_data.items():
                    event = device.get_event_by_name(event_name)
                    if event is None:
                        raise ModuleInitializationError('Event "{}" is not supported by device '
                                                        "#{} (class: {})".format(event_name, device_id,
                                                                                 device.module_name))
                    if isinstance(link_data, str):
                        link_data = [link_data]
                    for link_string in link_data:
                        linked_device_id, action_name = self.__parse_link_string(link_string)
                        # Check if event is supported by current device
                        # Find device in registry
                        if linked_device_id not in self.devices:
                            raise ModuleInitializationError("Unable to link device #{} to #{}: "
                                                            "#{} Doesn't exist".format(device_id, linked_device_id,
                                                                                       linked_device_id))
                        linked_device = self.devices.get(linked_device_id)
                        action = linked_device.get_action_by_name(action_name)
                        if action is None:
                            raise ModuleInitializationError("Action {} is not supported by "
                                                            "device #{} (class: {})".format(action_name,
                                                                                            linked_device_id,
                                                                                            linked_device.module_name))
                        device.pipe(event, linked_device, action)
                        self.logger.info('Piped event "{}" from #{} -> {}'.format(event_name, device_id, link_string))
            device.setup()
            device.initialized(True)
        self.after_initialization()

    def start(self):
        """
        Starts handling cycle
        """

        def on_step(device):
            while not threading.currentThread().terminating:
                try:
                    device.step()
                    sleep(float(self.step_interval) / 1000)
                except Exception as e:
                    self.logger.error('Execution failed for module {}: {}'.format(device, e))
            # when terminating
            device.shutdown()

        for device in self.devices.values():
            if not device.__class__.requires_thread:
                continue
            thread = Thread(target=on_step, name="device-#" + device.id, args=(device,))
            thread.terminating = False
            self.managed_threads.append(thread)
            thread.start()

    def stop(self):
        for x in self.managed_threads:
            try:
                x.terminating = True
            except Exception as e:
                self.logger.error("Unable to shutdown thread: {}".format(e))

    def after_initialization(self):
        pass
