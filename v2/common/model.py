from .errors import InvalidDriverError


class InstanceSettings:
    def __init__(self):
        self.id = None
        self.context_path = []


class Driver:
    @staticmethod
    def typeid() -> int:
        return -1

    @staticmethod
    def type_name() -> str:
        raise InvalidDriverError('Driver class should implement type_name() method')

    def on_initialized(self, application):
        """
        :type application: ApplicationManager
        :return:
        """
        pass

    def on_before_unloaded(self, application):
        """
        :type application: ApplicationManager
        :return:
        """
        pass


class EventDef:
    def __init__(self, id: int, name: str):
        super().__init__()
        self.id = id
        self.name = name


class ActionDef:
    def __init__(self, id: int, name: str, function):
        super().__init__()
        self.id = id
        self.name = name
        self.callable = function


class ParameterDef:
    def __init__(self, name: str, is_required=False, validators=None):
        super().__init__()
        self.name = name
        self.is_required = is_required
        self.validators = validators
        if self.validators is None:
            self.validators = []

    def cleanup_value(self, value):
        return value

    def validate(self, value):
        for x in self.validators:
            if not x(value):
                raise ValueError('Parameter {} is invalid'.format(self.name))


class Module:
    EVENTS = []
    ACTIONS = []
    PARAMS = []
    IN_LOOP = True  # Indicates that instance of of this module will be queried (step method) in main application loop
    MINIMAL_ITERATION_INTERVAL = 0  # Minimum interval between iterations in milliseconds

    def __init__(self, application):
        """
        :type application: ApplicationManager
        """
        self.id = None
        self.name = None
        self.__application = application
        self.last_step = 0

    def get_application_manager(self):
        """
        :rtype application: ApplicationManager
        """
        return self.__application

    @staticmethod
    def typeid() -> int:
        return -1

    @staticmethod
    def type_name() -> str:
        raise InvalidDriverError('Module class should implement type_name() method')

    def emit(self, event_id, data):
        pass

    def step(self):
        pass

    def on_initialized(self):
        pass

    def on_before_destroyed(self):
        pass

    def validate(self):
        pass
