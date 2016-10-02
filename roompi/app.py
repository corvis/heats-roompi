import logging.config
import sys
from time import sleep

import os
import yaml
from roompi import bootstrap
__author__ = 'LOGICIFY\corvis'

if __name__ == '__main__':
    logging.config.dictConfig(yaml.load(file('./logger.yaml', 'r')))
    config_file_name = './config.yaml'
    context_path = os.path.dirname(os.path.realpath(config_file_name))

    device_controller = None
    try:
        application_context = bootstrap.bootstrap(context_path, config_file_name)
        device_controller = application_context.device_controller
        device_controller.start()
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print "Terminating..."
        if device_controller is not None:
            device_controller.stop()
        exit()
