import logging
import logging.config
from unittest import TestCase
import yaml
from roompi.modules import registry

__author__ = 'LOGICIFY\corvis'


class ButtonsModuleSuit(TestCase):

    def test_valid_configuration(self):
        logging.config.dictConfig(yaml.load(file('./logger.yaml', 'r')))
        registry.autodiscover()
        config_file = file('./tests/resources/button_module_valid.yaml', 'r')
        config = yaml.load(config_file)
        modules = config.get('devices')
        module_config = modules['bedroom_switch']
        module_config['id'] = 'bedroom_switch'
        module = registry.create_module(module_config)
        self.assertEqual(module.gpio, 1)
        self.assertEqual(module.handle_double_click, True)
