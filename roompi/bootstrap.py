import datetime

import importlib
import logging
import sys

import os
import yaml
from roompi.controller.device import DeviceController, InstanceSettings, ApplicationContext
from roompi.controller.utils import resolve_path
from roompi.modules import registry
from roompi.modules.errors import ConfigurationError, DriverInitializationError

__logger = logging.getLogger('Bootstrap')


def bootstrap(context_path, config_file_name):
    start_time = datetime.datetime.now()
    __logger.info("Reading configuration")
    with open(config_file_name, 'r') as config_file:
        config = yaml.load(config_file)
    # Check general configuration options
    extra_classpath = []
    instance_config = InstanceSettings(config.get('instance'))
    # extend classpath
    if isinstance(instance_config.get('classpath'), list):
        for p in instance_config.get('classpath'):
            absolute_path = resolve_path(p, context_path)
            if os.path.isdir(absolute_path):
                extra_classpath.append(absolute_path)
                sys.path.append(absolute_path)
            else:
                __logger.warning("Unable to add directory {} to classpath".format(absolute_path))
    __logger.info("Initializing drivers...")
    application_context = ApplicationContext()
    __initialize_drivers(config, application_context)
    __logger.info("Discovering modules...")
    registry.autodiscover(extra_classpath)
    __logger.info("Registered {} modules".format(len(registry.modules.keys())))

    application_context.register_singleton(instance_config)
    DeviceController(config.get('devices', {}), application_context)
    init_time = datetime.datetime.now() - start_time
    __logger.info("Bootstrap finished in {} seconds".format(init_time.total_seconds()))
    return application_context


def __initialize_drivers(config, application_context):
    drivers = config.get('drivers', [])
    if not isinstance(drivers, list):
        raise ConfigurationError('Drivers section should be a list of objects')
    for driver_config in drivers:
        if not isinstance(driver_config, dict):
            raise ConfigurationError('Driver should be an object containing "class" field.')
        driver_class_name = driver_config.get('class')
        if not isinstance(driver_class_name, str):
            raise ConfigurationError("Can't read class for the driver_config definition: {}".format(driver_config))
        __logger.info('Loading driver_config {}'.format(driver_class_name))
        driver = None
        try:
            module_name, class_name = driver_class_name.rsplit('.', 1)
            module = importlib.import_module(module_name)
            driver_class = getattr(module, class_name, None)
            if driver_class is None:
                raise Exception("Module {} doesn't contain {} class", class_name)
            driver = driver_class()
        except Exception as e:
            raise DriverInitializationError(
                "Unable to load driver {} due to the following exception: {}".format(driver_class_name, e))
        application_context.register_driver(driver)
        try:
            driver.on_loaded(application_context)
        except Exception as e:
            raise DriverInitializationError(
                "Unable to initialize driver {} due to the following exception: {}".format(driver_class_name, e))
