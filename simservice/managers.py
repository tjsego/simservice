"""
Defines service managers
"""
from multiprocessing.managers import BaseManager
from typing import Callable, Dict, Optional


class _ServiceManagerLocal(BaseManager):
    pass


class ServiceManagerLocal:
    """Manager for locally-hosted services"""

    manager: Optional[_ServiceManagerLocal] = None
    """Underlying manager"""

    started: bool = False
    """Flag for whether the manager has been started"""

    service_registry = dict()
    """
    Registry of services
    
    type: Dict[str, service_wraps.TypeProcessWrap]
    """

    function_registry: Dict[str, Callable] = dict()
    """
    Register of functions
    """

    @staticmethod
    def _on_demand_manager():
        if ServiceManagerLocal.manager is None:
            ServiceManagerLocal.manager = _ServiceManagerLocal()
            print(f"Initialized service manager {ServiceManagerLocal.manager}")

    @classmethod
    def start(cls, *args, **kwargs):
        """Simple wrap of BaseManager.start"""
        cls._on_demand_manager()
        if not cls.started:
            cls.manager.start(*args, **kwargs)
            cls.started = True

    @classmethod
    def _register_callable(cls, _name, _callable):
        cls.manager.register(_name, _callable)
        manager = cls.manager
        impl = getattr(manager, _name)
        setattr(cls, _name, impl)

    @classmethod
    def register_service(cls, _service_name, _service_wrap):
        """
        Registers a service wrap with the manager

        :param _service_name: name of service
        :type _service_name: str
        :param _service_wrap: service wrap to register
        :type _service_wrap: service_wraps.TypeProcessWrap
        :return: None
        """
        cls._on_demand_manager()

        if _service_name in cls.service_registry.keys():
            raise AttributeError(f"Service with name {_service_name} has already been registered")

        cls.service_registry[_service_name] = _service_wrap
        cls._register_callable(_service_name, _service_wrap)

    @classmethod
    def register_function(cls, _function_name, _func):
        """
        Registers a function with the manager

        :param _function_name: name of function
        :type _function_name: str
        :param _func: function to register
        :type _func: Callable
        :return: None
        """
        cls._on_demand_manager()

        if _function_name in cls.function_registry.keys():
            raise AttributeError(f"Function with name {_function_name} has already been registered")

        cls.function_registry[_function_name] = _func
        cls._register_callable(_function_name, _func)

    @classmethod
    def shutdown(cls):
        """Shuts down the manager"""
        if cls.started:
            cls.manager.shutdown()
            cls.manager = None
            cls.started = False

    @classmethod
    def is_registered(cls, _name) -> bool:
        """
        Tests if a service has been registered

        :param _name: name of service or function
        :type _name: str
        :return: True if passed name is found in registry
        :rtype: bool
        """
        return _name in cls.service_registry.keys() or _name in cls.function_registry.keys()


def close_services():
    """
    Closes all service managers

    :return: None
    """
    ServiceManagerLocal.shutdown()
