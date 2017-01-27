import logging

from common.model import Module
from roompi.modules import ActionDefinition


class LoggerModule(Module):

    def __init__(self, application):
        super().__init__(application)
        self.__logger = None

    def on_initialized(self):
        self.__logger = logging.getLogger('L-' + self.name)
        self.__logger.info('Logging device initialized')

    def log(self, data=None, context=None):
        self.__logger.info('data={}, context={}'.format(data, context))

    @staticmethod
    def type_name() -> str:
        return 'Logger'

    @staticmethod
    def typeid() -> int:
        return 0x0101

    ACTIONS = [
        ActionDefinition('log', log),
    ]