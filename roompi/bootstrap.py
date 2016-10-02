import logging.config
import sys
from time import sleep

import os
import yaml
from roompi.controller.device import DeviceController, InstanceSettings, ApplicationContext
from roompi.controller.utils import resolve_path
from roompi.modules import registry


def bootstrap(context_path, config_file_name):
    logger = logging.getLogger('Bootstrap')
    config_file = file(config_file_name, 'r')
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
                logger.warning("Unable to add directory {} to classpath".format(absolute_path))
    logger.info("Discovering modules...")
    registry.autodiscover(extra_classpath)
    logger.info("Registered {} modules".format(len(registry.modules.keys())))
    application_context = ApplicationContext()
    application_context.register_singleton(instance_config)
    DeviceController(config.get('devices', {}), application_context)
    return application_context