from .. import RoomPiModule, registry, EventDefinition
from .. import parameters
from datetime import time
from roompi.modules.parameters import ParameterDefinition

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
except:
    import roompi.mock.GPIO as GPIO

__author__ = 'LOGICIFY\corvis'

RELEASED = 0
PRESSED = 1

# Events
EVENT_CLICK = 'click'
EVENT_LONG_CLICK = 'long_click'
EVENT_DOUBLE_CLICK = 'double_click'


class ButtonModule(RoomPiModule):
    module_name = 'Button'
    allowed_parameters = (
        parameters.GPIOParameter(name='gpio', description='GPIO port to bind to'),
        ParameterDefinition(name='notify_server',
                            description='This option indicates if module should notify server'
                                        'on each event this module raises.',
                            validators=(parameters.boolean_validator,),
                            is_required=False),
        ParameterDefinition(name='handle_long_click',
                            description='If this option is enabled, module will try to '
                                        'handle long click event.',
                            validators=(parameters.boolean_validator,),
                            is_required=False),
        ParameterDefinition(name='handle_double_click',
                            description='If this option is enabled, module will try to '
                                        'handle double click event.',
                            validators=(parameters.boolean_validator,),
                            is_required=False),
        ParameterDefinition(name='long_click_duration',
                            description='In case when handle_long_click is enabled '
                                        'this option defines a time while button should '
                                        'be pressed to be interpreted as long click',
                            validators=(parameters.integer_validator,),
                            is_required=False),
        ParameterDefinition(name='double_click_duration',
                            description='In case when handle_double_click is enabled '
                                        'this option defines max duration between clicks',
                            validators=(parameters.integer_validator,),
                            is_required=False),
    )
    events = (
        EventDefinition('click', 'Fired when device detects single click on the button'),
        EventDefinition('double_click', 'Fired when device detects double click on the button'),
        EventDefinition('long_click', 'Fired when device detects long pressing of the button'),
    )

    def __init__(self):
        super(ButtonModule, self).__init__()
        self.gpio = None
        self.notify_server = False
        self.handle_long_click = False
        self.handle_double_click = False
        self.long_click_duration = 1000
        self.double_click_duration = 400
        self.__wait_until_released = False
        self.__prev_state = RELEASED
        self.__click_time = 0
        self.__pressed_time = 0
        self.__released_time = 0


    @property
    def ignore_complex_events(self):
        return not self.handle_long_click and not self.handle_double_click

    def register_new_state(self, state):
        if state != self.__prev_state:
            if self.__prev_state == RELEASED:
                self.__pressed_time = self.get_current_time()
            else:
                self.__released_time = self.get_current_time()

    def setup(self):
        GPIO.setup(self.gpio, GPIO.IN)

    def step(self):
        state = GPIO.input(self.gpio)
        if self.__wait_until_released:
            if state == RELEASED:
                self.__wait_until_released = False
            else:
                return
        self.logger.debug('GPIO STATE: {0}'.format(state))
        self.register_new_state(state)
        if self.handle_long_click and state == PRESSED:
            if self.__pressed_time > 0 and self.get_current_time() - self.__pressed_time >= self.long_click_duration:
                self.__pressed_time = 0
                self.__released_time = 0
                self.__prev_state = RELEASED
                self.__wait_until_released = True
                self.emit(EVENT_LONG_CLICK)
                return
        if self.__prev_state == PRESSED and state == RELEASED:
            if self.handle_double_click:
                if self.__click_time > 0 and self.get_current_time() - self.__click_time <= self.double_click_duration:
                    self.__pressed_time = 0
                    self.__released_time = 0
                    self.__prev_state = RELEASED
                    self.__click_time = 0
                    self.emit(EVENT_DOUBLE_CLICK)
                    return
                elif self.__click_time == 0:
                    #print "First click"
                    self.__click_time = self.get_current_time()
                else:
                    self.emit(EVENT_CLICK)
            else:
                self.emit(EVENT_CLICK)
        # Reset click counter if timeout reached
        if state == RELEASED and self.handle_double_click and self.__click_time > 0 \
                and self.get_current_time() - self.__click_time > self.double_click_duration:
            #print "Click reset"
            self.__click_time = 0
            self.emit(EVENT_CLICK)
        self.__prev_state = state


registry.register(ButtonModule)