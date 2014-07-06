from roompi.modules import RoomPiModule, ActionDefinition

__author__ = 'LOGICIFY\corvis'


class DeviceStateMessage:
    def __init__(self, device, state):
        self.device = device
        self.state = state


class CommunicationBusModule(RoomPiModule):
    module_name = 'CommunicationBus'
    requires_thread = False
    actions = (
        ActionDefinition('push', description='Publishes given command'),
        ActionDefinition('push_state', description='Publishes information device state information'),
    )
    events = (

    )

    def action_push(self, data=None, context=None):
        pass

    def action_push_state(self, data=None, context=None):
        event_emitter = context.get('emitter', None)
        if event_emitter is None:
            self.logger.error("Unable to determine event emitter... Something is going terribly wrong!")
            return
        device_state_message = DeviceStateMessage(event_emitter, data)
        # Todo: Send message!
