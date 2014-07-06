from .. import RoomPiModule, ActionDefinition, registry, parameters, EventDefinition

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
except:
    import roompi.mock.GPIO as GPIO

__author__ = 'LOGICIFY\corvis'


class PowerKeyModule(RoomPiModule):
    STATE_ON = 1
    STATE_OFF = 0

    module_name = 'PowerKey'
    requires_thread = True
    allowed_parameters = (
        parameters.GPIOParameter(name='gpio', description='GPIO port to bind to'),
    )
    actions = (
        ActionDefinition('toggle', 'Toggles value of the switch'),
        ActionDefinition('off', 'Breaks the power line'),
        ActionDefinition('on', 'Commutes the power line'),
    )

    events = (
        EventDefinition('state_changed', 'Will be emitted once power line commutation changes state')
    )

    def __init__(self):
        super(PowerKeyModule, self).__init__()
        self.gpio = None
        self.current_state = 0

    def setup(self):
        GPIO.setup(self.gpio, GPIO.OUT)
        print "power setup"
        self.action_set_state(self.STATE_OFF)

    def action_set_state(self, state):
        GPIO.output(self.gpio, state)
        self.current_state = state
        self.emit('state_changed', dict(current_state=self.current_state))

    def action_toggle(self, data=None, context=None):
        new_state = self.STATE_ON if self.current_state == self.STATE_OFF else self.STATE_OFF
        self.action_set_state(new_state)

    def action_off(self, data=None, context=None):
        self.action_set_state(self.STATE_OFF)

    def action_on(self, data=None, context=None):
        self.action_set_state(self.STATE_ON)

registry.register(PowerKeyModule)