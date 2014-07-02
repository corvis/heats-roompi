from .. import RoomPiModule, ActionDefinition, registry

__author__ = 'LOGICIFY\corvis'


class LoggerModule(RoomPiModule):
    module_name = 'Logger'
    actions = (
        ActionDefinition('log', 'Records received data along with event name in log'),
    )

    def action_log(self, data=None, context=None):
        self.logger.info('data={}, context={}'.format(data, context))

registry.register(LoggerModule)