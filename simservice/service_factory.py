"""
Defines a factory method for instantiating services
"""
from multiprocessing import Pipe

from . import managers
from .ServiceFunctionReceiver import ServiceFunctionReceiver


def connect_properties(_client_process, _server_wrap_class) -> None:
    """
    Connect properties of a wrapped service class to a client process class

    Wrapped service class should present a list of properties via a method *_property_names()* and corresponding
    getter and setter methods.

    E.g., for ``p`` in ``cls._property_names()``, ``cls.get_p()`` and ``cls.set_p()`` are defined

    :param _client_process: client-side service proxy instance
    :param _server_wrap_class: server-side wrapped service class
    :return: None
    """
    for p in _server_wrap_class._property_names():
        _fget = getattr(type(_client_process), f"get_{p}")
        _fset = getattr(type(_client_process), f"set_{p}")
        setattr(type(_client_process), p, property(fget=_fget, fset=_fset, fdel=None))


class ProcessRegistry:
    """
    A registry of process info

    Acts as a dictionary, where each key is the name of a registered service,
    and each value is a tuple of the following,

    - the service process
    - the service wrap
    - connection to the service process
    - connection to service function receiver
    """

    _items = dict()
    """Underlying data"""

    @classmethod
    def __getitem__(cls, item):
        return cls._items[item]

    @classmethod
    def __setitem__(cls, key, value):
        cls._items[key] = value

    @classmethod
    def __delitem__(cls, key):
        cls._items.__delitem__(key)


process_registry = ProcessRegistry()


def get_proxy_by_process_name(_process_name: str):
    """
    Returns a process by name

    :param _process_name: name of process
    :type _process_name: str
    :return:
    :rtype:
    """
    return process_registry[_process_name]


def close_service(_s) -> None:
    """
    Closes a service completely

    :param _s: service proxy
    """
    _s.close()
    del process_registry[_s.process_name()]
    ServiceFunctionReceiver.disconnect_service(_s)


def registered_services():
    """
    Returns the list of registered services
    """
    manager_local = managers.ServiceManagerLocal
    return list(manager_local.service_registry.keys()) + list(manager_local.function_registry.keys())


def running_processes():
    """
    Returns the list of names of all known running processes
    """
    return list(process_registry._items.keys())


def process_factory(_service_name: str, *args, **kwargs):
    """
    Main template service process proxy generator for local services

    Implementations should work through this when presenting a service proxy

    :param _service_name: basic name of service; the factory will generate a unique name for each instance
    :type _service_name: str
    :param args: service constructor position arguments
    :param kwargs: service constructor keyword arguments
    :return: service proxy instance
    """
    manager_local = managers.ServiceManagerLocal
    # Check that service has been locally registered
    # Implementation should have already registered the service with the local manager via register_service
    assert manager_local.is_registered(_service_name)

    # Start the local manager; wrap handles multiple calls to start()
    manager_local.start()

    # Instantiate client service and store process info and connection
    factory_conn, return_conn = Pipe()
    client_proc = getattr(manager_local, _service_name)(return_conn, *args, **kwargs)
    _process_name, process_conn, sfunc_receiver_conn = factory_conn.recv()
    # Connect properties defined on service class
    _cls_wrap = manager_local.service_registry[_service_name]
    connect_properties(client_proc, _cls_wrap)
    # Store useful info
    process_registry[_process_name] = (client_proc, _cls_wrap, process_conn, sfunc_receiver_conn)
    # Register service function with receiver
    ServiceFunctionReceiver.register_service(client_proc, sfunc_receiver_conn)
    return client_proc
