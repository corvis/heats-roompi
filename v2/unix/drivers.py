import logging

import paho.mqtt.client as mqtt

from common.drivers import GPIODriver, DataChannelDriver
from roompi.modules.errors import ConfigurationError


class FakeGPIODriver(GPIODriver):
    def __init__(self):
        self.__logger = logging.getLogger('FakeGPIODriver')

    def read(self, pin: int) -> int:
        return 0

    def set(self, pin: int, state: int):
        self.__logger.info("Set pin {}: {}".format(pin, state))


class MQTTDriver(DataChannelDriver):
    class MQTTChannel(DataChannelDriver.Channel):

        class Callback:
            @staticmethod
            def create_on_connect_callback(channel):
                """
                :type channel: MQTTDriver.MQTTChannel
                :return: Callable
                """

                def cb(client, userdata, flags, rc):
                    channel.logger.info("Connected to MQTT server: Code: " + str(rc))
                    if not channel._was_connected:
                        channel._was_connected = True
                    channel._connected = True
                    client.subscribe("$SYS/#")

                return cb

            @staticmethod
            def create_on_disconnect_callback(channel):
                """
                :type channel: MQTTDriver.MQTTChannel
                :return: Callable
                """

                def cb(client, userdata, rc):
                    channel.logger.info("Disconnected from MQTT server: Code: " + str(rc))
                    channel._connected = False

                return cb

            # The callback for when a PUBLISH message is received from the server.
            @staticmethod
            def create_on_message_callback(channel):
                """
                :type channel: MQTTDriver.MQTTChannel
                :return: Callable
                """

                def cb(client, userdata, msg):
                    try:
                        pass
                    except Exception as e:
                        channel.logger.error(
                            'Unable to handle message: ' + msg.topic + ", msg: " + str(msg.payload) + ', error: ' + str(
                                e))

                return cb

        def __init__(self, driver, connection_options: dict):
            """
            :type driver: MQTTDriver
            """
            super().__init__(connection_options)
            self.logger = driver.logger
            self._connected = False
            self._was_connected = False
            self._thread = None
            try:
                self.bind_address = connection_options.get('bind_address', '0.0.0.0')
                self.server_address = connection_options.get('server_address', '127.0.0.1')
                self.server_port = connection_options.get('port', 1883)
            except KeyError as e:
                raise ConfigurationError("Unable to build MQTT communication channel because of configuration error: "
                                         + str(e))
            self._mqtt_client = mqtt.Client()
            self._mqtt_client.on_connect = self.Callback.create_on_connect_callback(self)
            self._mqtt_client.on_disconnect = self.Callback.create_on_disconnect_callback(self)
            self._mqtt_client.on_message = self.Callback.create_on_message_callback(self)

        def send(self, data):
            super().send(data)

        def is_connected(self) -> bool:
            return self._connected

        def connect(self):
            if not self._was_connected:
                self._mqtt_client.connect_async(self.server_address, port=self.server_port,
                                                bind_address=self.bind_address)
            self._mqtt_client.reconnect()

        def step(self):
            try:
                self._mqtt_client.loop()
            except Exception as e:
                pass

        def disconnect(self):
            self._mqtt_client.disconnect()

    def __init__(self):
        super().__init__()
        self.__thread_manager = None  # type: common.core.ThreadManager
        self.__channel_counter = 0

    def on_initialized(self, application):
        """
        :type application: common.core.ApplicationManager
        :return:
        """
        self.__thread_manager = application.thread_manager

    def new_channel(self, connection_options: dict) -> MQTTChannel:
        def do_step(channel):
            channel.step()

        channel = MQTTDriver.MQTTChannel(self, connection_options)
        self.__channel_counter += 1
        thread = self.__thread_manager.request_thread('MQTTDriver-ch' + str(self.__channel_counter), channel.step, [])
        channel.dispose = lambda: self.__thread_manager.dispose_thread(thread)
        return channel
