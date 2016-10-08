import logging
import pkgutil
import time

from . import parameters
from roompi.modules.errors import ModuleInitializationError

__author__ = 'LOGICIFY\corvis'

ACTION_METHOD_PREFIX = 'action_'


class EventDefinition(object):
    def __init__(self, name, description=''):
        self.name = name
        self.description = description

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'Event<{}>'.format(self.name)


class ActionDefinition(object):
    def __init__(self, name, description=''):
        self.name = name
        self.description = description

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'Action<{}>'.format(self.name)


class PipedEvent(object):
    """
    This class represents the event of which can be raised by device and action which should be executed
    """

    def __init__(self, event_emitter, event, linked_device, action):
        """
        @var self.event_emitter: Device which raises an event
        @var self.event: Target event
        @var self.linked_device: Linked device
        @var self.action: Action to be executed on linked device

        @type self.event: EventDefinition
        @type self.event_emitter: RoomPiModule
        @type self.linked_device: RoomPiModule
        @type self.ActionDefinition: ActionDefinition
        """
        self.event_emitter = event_emitter
        self.event = event
        self.linked_device = linked_device
        self.action = action
        self.__action_function = None
        if self.action is not None:
            self.__action_function = getattr(self.linked_device, ACTION_METHOD_PREFIX + action.name)

    def invoke(self, **arguments):
        if self.__action_function is not None:
            self.__action_function(data=arguments, context=dict(event=self.event,
                                                                emitter=self.event_emitter))


class RoomPiModule(object):
    module_name = None
    allowed_parameters = []
    events = []
    actions = []
    depends_on = []
    requires_thread = True

    def __init__(self):
        self.id = ''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.piped_events = {}
        self.__application_context = None

    def __str__(self):
        return '#{} (class: {})'.format(self.id, self.module_name)

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def get_current_time():
        return int(round(time.time() * 1000))

    @classmethod
    def get_action_by_name(cls, action_name):
        """
        Finds an action in the list of supported actions and returns it as result
        @rtype: ActionDefinition
        @return: Action or None
        """
        for x in cls.actions:
            if x.name == action_name:
                return x
        return None

    @property
    def application_context(self):
        """
        @rtype: roompi.controller.device.ApplicationContext
        """
        return self.__application_context

    @application_context.setter
    def application_context(self, value):
        """
        @type value: roompi.controller.device.ApplicationContext
        """
        self.__application_context = value

    def action(self, action, **arguments):
        if isinstance(action, str):
            action_obj = self.get_action_by_name(action)
        else:
            action_obj = action
        if action_obj is None:
            raise RuntimeError('Action {} is not supported by device #{} (class: {})'.format(action, self.id,
                                                                                             self.module_name))
        action_function = getattr(self, ACTION_METHOD_PREFIX + action.name)
        return action_function(arguments, context=None)

    @classmethod
    def get_event_by_name(cls, event_name):
        for x in cls.events:
            if x.name == event_name:
                return x
        return None

    def pipe(self, event, linked_device, action):
        """
        Creates binding between event raised by this device and action which will be executed on linked device
        """
        piped_event = PipedEvent(
            event_emitter=self,
            event=event,
            linked_device=linked_device,
            action=action
        )
        if event.name not in self.piped_events:
            self.piped_events[event.name] = []
        self.piped_events[event.name].append(piped_event)

    def validate(self):
        """
        This method will be invoked by module registry after initialization.
        It shuold be defined in concrete module class and raise ModuleInitializationError in case when
        instance is not valid.
        """
        return True

    def emit(self, event_name, **data):
        """
        Raises event and passes given data as arguments
        """
        # Bubble event to the piped devices
        if event_name in self.piped_events:
            for piped_event in self.piped_events[event_name]:
                try:
                    piped_event.invoke(**data)
                except Exception as e:
                    self.logger.error("Error during execution of piped action: " + str(e))
        self.logger.info("EMITTED EVENT:" + event_name + str(data))

    def setup(self):
        """
        This method will be invoked only once, after initialization
        """
        pass

    def step(self):
        """
        This method will be invoked on each processing step. By default 50 millis.
        """
        pass

    @classmethod
    def from_dict(cls, dictionary, application_context):
        dependencies = {}
        if cls.depends_on is not None:
            for x in cls.depends_on:
                dep = application_context.get(x, None)
                if dep is None:
                    raise ModuleInitializationError("Module {} depends on {}, which is not available".format(cls.module_name, x))
                dependencies[x] = dep
        instance = cls(**dependencies)
        instance.application_context = application_context
        # Fetching module id
        if 'id' in dictionary:
            if parameters.module_id_validator(dictionary.get('id')):
                instance.id = dictionary.get('id')
            else:
                raise ModuleInitializationError('Module has invalid ID: ' + dictionary.get('id'))
        else:
            raise ModuleInitializationError('Device ID is not set')
        # Parsing parameters
        for x in instance.allowed_parameters:
            if x.name not in dictionary:
                if x.is_required:
                    raise ModuleInitializationError('Module {0} Parameter {1}'.format(cls.module_name, x.name))
                else:
                    continue
            value = dictionary.get(x.name)
            x.validate(value)
            setattr(instance, x.name, x.clean_value(value))
        # Validate all action methods
        for action in cls.actions:
            if hasattr(instance, ACTION_METHOD_PREFIX + action.name):
                # TODO: Maybe it makes sense to check function signature...
                pass
            else:
                raise ModuleInitializationError("Module class {} declares action {} but doesn't "
                                                "provide corresponding handler".format(cls.module_name, action.name))
        return instance


class ModuleRegistry(object):
    def __init__(self):
        self.modules = {}
        self.__logger = logging.getLogger('ModuleRegistry')
        self.__modules_autodiscovered = False

    def register(self, moduleCls):
        if moduleCls.module_name in self.modules:
            raise Exception('This module({}) is already registered'.format(moduleCls.name))
        if not issubclass(moduleCls, RoomPiModule):
            raise Exception('Only subclasses of RoomPiModule can be registered')
        module_name = moduleCls.module_name
        self.modules[module_name] = moduleCls
        self.__logger.info('Registered module class "{}"'.format(module_name))

    def create_module(self, configuration, application_context=None):
        if 'module_name' not in configuration:
            raise ModuleInitializationError('Module name is not defined')
        if configuration['module_name'] not in self.modules:
            raise ModuleInitializationError('Module {} is unknown'.format(configuration['module_name']))
        module_cls = self.modules[configuration.get('module_name')]
        module = module_cls.from_dict(configuration, application_context)
        module.validate()
        self.__logger.info("Initialized device #{}. Type: {}".format(module.id, module_cls.module_name))
        return module

    def autodiscover(self, classpath=None):
        """
        :param classpath: array of extra locations which should be searched for modules.
                          default modules from roompi.modules dir will be used regardless of this setting
        :type classpath: list[string]
        """
        if self.__modules_autodiscovered:
            return
        __all__ = []
        dirs_to_search = list(__path__)
        if classpath is not None:
            for x in classpath:
                dirs_to_search.append(x)
        is_system_path = True
        for location in dirs_to_search:
            for loader, module_name, is_pkg in pkgutil.walk_packages([location]):
                if is_pkg:
                    __all__.append(module_name)
                    full_name = module_name
                    if is_system_path:
                        full_name = '.'.join((__name__, module_name))
                    __import__(full_name, globals(), locals())
            is_system_path = False
        self.__modules_autodiscovered = True


registry = ModuleRegistry()
