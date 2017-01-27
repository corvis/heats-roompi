import sys

import gc
import logging
import os.path
from common.drivers import ModuleDiscoveryDriver
from common.utils import int_to_hex4str
from modules import StandardModulesOnlyDriver
from .errors import ConfigValidationError, InvalidDriverError
from .core import ApplicationManager

MODULE_DISCOVERY_DRIVER = ModuleDiscoveryDriver.typeid()

__logger = logging.getLogger('Bootstrap')


def bootstrap(config: dict) -> ApplicationManager:
    application = ApplicationManager()
    # Save instance config
    __logger.info('Reading config file')
    __save_instance_config(config, application)
    __load_context_path(application)
    __logger.info('Config captured')
    gc.collect()
    # Load drivers
    __logger.info('Loading drivers')
    __load_drivers(config, application)
    __logger.info('Drivers loaded')
    gc.collect()
    # Discover modules
    module_discovery_driver = application.get_driver(MODULE_DISCOVERY_DRIVER)
    module_discovery_driver.discover_modules(application.get_module_registry())
    # Instantiate components
    devices_and_configs = __instantiate_devices(config, application)
    # Build pipe table

    # Initialize components

    # Compose main loop

    return application


def __save_instance_config(config: dict, application: ApplicationManager):
    if 'instance' in config:
        settings = application.get_instance_settings()
        settings.id = config.get('id')
        # Context Path
        for path in config.get('context_path', []):
            if isinstance(path, str):
                if not os.path.exists(path):
                    raise ConfigValidationError('instance/context_path', 'path ' + path + ' doesn\'t exist')
                settings.context_path.append(path)
            else:
                raise ConfigValidationError('instance/context_path', 'Context path should be the list of strings')


def __load_context_path(application: ApplicationManager):
    context_path = application.get_instance_settings().context_path
    for p in context_path:
        sys.path.append(p)


def __load_drivers(config: dict, application: ApplicationManager):
    drivers = config.get('drivers', [])
    for d in drivers:
        driver_class_name = None
        if isinstance(d, str):
            driver_class_name = d
        elif isinstance(d, dict) and 'class' in d:
            driver_class_name = d.get('class')
        if driver_class_name is None:
            raise ConfigValidationError('drivers', 'Section is invalid')
        application.register_driver(driver_class_name)
    # Check if there is module discovery driver loaded. If not - load default implementation
    try:
        application.get_driver(MODULE_DISCOVERY_DRIVER)
    except InvalidDriverError:
        __logger.info("Since no module discovery driver provided only standard modules might be used")
        application.register_driver(StandardModulesOnlyDriver)


def __instantiate_devices(config: dict, application: ApplicationManager) -> list:
    devices_with_config = []
    devices = config.get('devices', {})
    counter = 0x0200
    for name, device_def in devices.items():
        if not (isinstance(device_def, dict) or 'module_name' in device_def):
            raise ConfigValidationError('devices/' + name, 'Should be dictionary containing mandatory module_name key')
        module_registry = application.get_module_registry()
        instance = module_registry.create_module_instance(
            application,
            typeid=module_registry.find_module_by_name(device_def.get('module_name')).typeid(),
            instance_name=name,
            instance_id=counter + 1
        )
        try:
            # Parse and set parameters
            for param_def in instance.PARAMS:
                if param_def.name in device_def:
                    val = device_def[param_def.name]
                    param_def.validate(val)
                    setattr(instance, param_def.name, val)
                elif param_def.is_required:
                    raise ConfigValidationError('Parameter {} is required'.format(param_def.name))
            # Run validation of the overall device
            instance.validate()
            instance.on_initialized()
        except Exception as e:
            raise ConfigValidationError("devices/" + name, "Invalid device configuration: " + str(e), e)
        application.register_device(instance)
        devices_with_config.append((instance, device_def))
        __logger.debug("Initialized device {}({}). Type: {}({})".format(int_to_hex4str(instance.id), instance.name, int_to_hex4str(instance.typeid()), instance.type_name()))
        counter += 1
    return devices_with_config


def __build_pipes(devices_and_configs, application):
    pass
