import logging
import logging.config
from time import sleep
import yaml
from roompi.controller.device import DeviceController

__author__ = 'LOGICIFY\corvis'

if __name__ == '__main__':
    device_controller = None
    try:
        logging.config.dictConfig(yaml.load(file('./logger.yaml', 'r')))
        config_file = file('./config.yaml', 'r')
        config = yaml.load(config_file)
        devices = config['devices']
        device_controller = DeviceController(devices)
        device_controller.start()
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print "Terminating..."
        if device_controller is not None:
            device_controller.stop()
        exit()