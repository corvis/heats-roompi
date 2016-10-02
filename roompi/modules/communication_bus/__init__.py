from roompi.modules import RoomPiModule, ActionDefinition, EventDefinition, ModuleInitializationError, registry

__author__ = 'LOGICIFY\corvis'


class DeviceStateMessage(object):
    def __init__(self, device, state):
        self.device = device
        self.state = state


class RemoteCommand(object):
    def __init__(self):
        self.device = None
        self.action_name = None
        self.arguments = {}


class CommunicationBusModule(RoomPiModule):
    module_name = 'CommunicationBus'
    requires_thread = False
    actions = (
        ActionDefinition('push', description='Publishes given command'),
        ActionDefinition('push_state', description='Publishes information device state information'),
    )
    events = (
        EventDefinition('remote_command_received',
                        'Fired when remote server request an action to be executed on some device'),
    )

    def __init__(self):
        super(CommunicationBusModule, self).__init__()
        self.device_controller = None

    def validate(self):
        # Check if DeviceController exists in application context
        if self.application_context.get('DeviceController') is None:
            raise ModuleInitializationError("DeviceController should be in application context")
        return True

    def setup(self):
        self.device_controller = self.application_context.get('DeviceController')

    def action_push(self, data=None, context=None):
        pass

    def action_push_state(self, data=None, context=None):
        event_emitter = context.get('emitter', None)
        if event_emitter is None:
            self.logger.error("Unable to determine event emitter... Something is going terribly wrong!")
            return
        device_state_message = DeviceStateMessage(event_emitter, data)
        # Todo: Send message!

    def remote_command_listener(self):
        """
        Listens for remote command and executes an action on some device
        """
        pass


registry.register(CommunicationBusModule)
