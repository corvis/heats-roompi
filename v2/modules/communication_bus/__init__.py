from typing import Dict

from common.drivers import DataChannelDriver
from common.model import Module, ParameterDef, ActionDef, Driver
from common import validators

ACTION_PUSH = 0x01
ACTION_PUSH_STATE = 0x02


class CommunicationBusModule(Module):
    TOPIC_PREFIX = 'rmod'
    TOPIC_STATE_SUFFIX = '/state'
    TOPIC_ACTION_SUFFIX = '/action'
    DEFAULT_BROKER_PORT = 2131

    @staticmethod
    def typeid() -> int:
        return 0x0110

    @staticmethod
    def type_name() -> str:
        return 'CommunicationBus'

    def __init__(self, application, drivers: Dict[int, Driver]):
        super().__init__(application, drivers)
        self.server_address = ''
        self.server_port = self.DEFAULT_BROKER_PORT
        self.bind_address = ''
        self._channel_driver = drivers.get(DataChannelDriver.typeid())  # type: DataChannelDriver
        self.channel = None # type: DataChannelDriver.Channel

    def push(self, data=None, context=None):
        if self.channel.is_connected():
            self.channel.send(data)

    def push_state(self, data=None, context=None):
        pass

    def on_initialized(self):
        self.channel = self._channel_driver.new_channel({
            "server_address": self.server_address,
            "server_port": self.server_port,
            "bind_address": self.bind_address,
        })

    def step(self):
        # We just need to check if connection is alive. If not - reconnect
        if not self.channel.is_connected():
            self.channel.connect()

    def on_before_destroyed(self):
        self.channel.disconnect()
        self.channel.dispose()

    ACTIONS = [
        ActionDef(ACTION_PUSH, 'push', push),
        ActionDef(ACTION_PUSH_STATE, 'push_state', push_state)
    ]

    PARAMS = [
        ParameterDef(name='server_address', is_required=True),
        ParameterDef(name='server_port', is_required=False, validators=[validators.integer]),
        ParameterDef(name='bind_address', is_required=False)
    ]
    IN_LOOP = True
    REQUIRED_DRIVERS = [DataChannelDriver.typeid()]
    MINIMAL_ITERATION_INTERVAL = 10 * 1000