from roompi.modules.errors import ModuleInitializationError

__author__ = 'LOGICIFY\corvis'


def boolean_validator(value):
    return isinstance(value, bool)


def integer_validator(value):
    return isinstance(value, (int, long))


def module_id_validator(value):
    return True


class ParameterDefinition(object):
    """
    Describes parameter for RoomPi module. Defines name, description, validation rules
    """

    def __init__(self, name='', description='', is_required=False, validators=None):
        super(ParameterDefinition, self).__init__()
        self.name = name
        self.description = description
        self.validators = validators
        self.is_required = is_required
        if self.validators is None:
            self.validators = []

    def clean_value(self, value):
        return value

    def validate(self, value):
        for x in self.validators:
            if not x(value):
                raise ModuleInitializationError('Invalid value for ' + self.name)


class GPIOParameter(ParameterDefinition):
    def __init__(self, name='', description=''):
        def validate_gpio_port(value):
            return value
        super(GPIOParameter, self).__init__(name, description, (validate_gpio_port,))
