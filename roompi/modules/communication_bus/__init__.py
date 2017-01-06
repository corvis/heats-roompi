import json

from roompi.modules import RoomPiModule, ActionDefinition, EventDefinition, ModuleInitializationError, registry
import paho.mqtt.client as mqtt
import roompi.modules.parameters as parameters

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


class MessageEncoder(object):
    def encode(self, payload):
        pass

    def decode(self, payload):
        pass

    def can_decode(self, payload):
        pass


class JsonMessageEncoder(MessageEncoder):
    def encode(self, payload):
        return json.dumps(payload, indent=0)

    def decode(self, payload):
        return json.loads(payload)

    def can_decode(self, payload):
        return isinstance(payload, str) and payload.startswith('{')


class CommunicationBusModule(RoomPiModule):
    TOPIC_PREFIX = 'rpi'
    TOPIC_STATE_SUFFIX = '/state'
    TOPIC_ACTION_SUFFIX = '/action'
    DEFAULT_BROKER_PORT = 2131

    module_name = 'CommunicationBus'
    requires_thread = True
    allowed_parameters = (
        parameters.ParameterDefinition(name='server_address', description='Address of the MQTT broker',
                                       is_required=True),
        parameters.ParameterDefinition(name='server_port',
                                       description='MQTT broker port, default is ' + str(DEFAULT_BROKER_PORT),
                                       is_required=False, validators=[parameters.integer_validator]),
        parameters.ParameterDefinition(name='bind_address', is_required=False)
    )
    actions = (
        ActionDefinition('push', description='Publishes given command'),
        ActionDefinition('push_state', description='Publishes device state information'),
    )
    events = (
        EventDefinition('remote_command_received',
                        'Fired when remote server request an action to be executed on some device'),
    )

    class Callback:
        # The callback for when the client receives a CONNACK response from the server.
        @staticmethod
        def on_connect(bus):
            def cb(client, userdata, flags, rc):
                bus.logger.info("Connected with result code " + str(rc))
                client.subscribe("$SYS/#")

            return cb

        # The callback for when a PUBLISH message is received from the server.
        @staticmethod
        def on_message(bus):
            def cb(client, userdata, msg):
                try:
                    if msg.topic.startswith(bus.topic_prefix) and (bus.TOPIC_ACTION_SUFFIX + '/' in msg.topic):
                        device_name, action = msg.topic.replace(bus.topic_prefix, '', 1).split(
                            bus.TOPIC_ACTION_SUFFIX + '/')
                        payload = None
                        if len(msg.payload) > 0:
                            try:
                                payload_str = str(msg.payload, 'utf-8')
                                if bus.message_encoder.can_decode(payload_str):
                                    payload = bus.message_encoder.decode(payload_str)
                                else:
                                    payload = payload_str
                            except ValueError:
                                bus.logger.exception("Unable to parse message: " + msg.topic + " " + str(msg.payload))
                                return
                        if device_name in bus.device_controller.devices:
                            # TODO: Add payload support
                            bus.device_controller.devices.get(device_name).action(action)
                        else:
                            bus.logger.warning(
                                "Got action command on unknown device: Device: " + device_name + ", action: " + action)
                except Exception as e:
                    bus.logger.error(
                        'Unable to handle message: ' + msg.topic + ", msg: " + str(msg.payload) + ', error: ' + str(e))

            return cb

    def __init__(self):
        super(CommunicationBusModule, self).__init__()
        self.device_controller = None
        self.client = mqtt.Client()
        self.topic_prefix = None
        self.server_address = 'localhost'
        self.server_port = 1883
        self.bind_address = ''
        self.message_encoder = JsonMessageEncoder()

    def validate(self):
        # Check if DeviceController exists in application context
        if self.application_context.get('DeviceController') is None:
            raise ModuleInitializationError("DeviceController should be in application context")
        return True

    def setup(self):
        self.device_controller = self.application_context.get('DeviceController')
        self.topic_prefix = "{}/{}/".format(self.TOPIC_PREFIX,
                                            self.application_context.get("InstanceSettings").instance_id)
        self.client.on_connect = self.Callback.on_connect(self)
        self.client.on_message = self.Callback.on_message(self)
        self.client.connect(self.server_address, self.server_port, 60, self.bind_address)
        self.client.subscribe(self.topic_prefix + '+' + self.TOPIC_ACTION_SUFFIX + '/+')

    def step(self):
        self.client.loop()

    def action_push(self, data=None, context=None):
        pass

    def action_push_state(self, data=None, context=None):
        event_emitter = context.get('emitter', None)
        if event_emitter is None:
            self.logger.error("Unable to determine event emitter... Something is going terribly wrong!")
            return
        device_state_message = DeviceStateMessage(event_emitter, data)
        try:
            result, mid = self.client.publish(self.topic_prefix + event_emitter.id + self.TOPIC_STATE_SUFFIX,
                                              self.message_encoder.encode(data))
        except Exception as e:
            self.logger.exception("Unable to publish event", e)

    def shutdown(self):
        self.logger.info("Disconnecting MQTT...")
        self.client.disconnect()
        self.logger.info("MQTT connection closed")

registry.register(CommunicationBusModule)
