"""
Defines structures for connecting service functions
"""
from threading import Thread
from typing import Dict

from .messages import safe_transmit


class _ServiceFunctionContainer:
    """
    Container for holding service functions by service proxy
    """
    def __init__(self):
        self._sfuncs = dict()
        """
        Service function storage
        
        type: Dict[str, messages.RemoteFunctionEvaluator]
        """

    def _register_function(self, function_name: str, evaluator):
        """
        Register service function

        :param function_name: name of function
        :type function_name: str
        :param evaluator: remote function evaluator
        :type evaluator: messages.RemoteFunctionEvaluator
        :return: None
        """
        self._sfuncs[function_name] = evaluator
        setattr(self, function_name, evaluator)


class _ServiceFunctionConnectionWorker(Thread):
    """
    An instance watches a registry-receiver connection, notifies the receiver that there's work to do and adds a
    newly registered service function to a service proxy instance
    """
    def __init__(self, _service_name, _sfunc_reg_conn, _conn_flusher, _sfunc_container, _attr_adder):
        """

        :param _service_name: name of service
        :type _service_name: str
        :param _sfunc_reg_conn: connection to service function registry
        :type _sfunc_reg_conn: multiprocessing.connection.Connection
        :param _conn_flusher: connection flusher, which processes all pending service function registrations in the
            Pipe of a service process
        :type _conn_flusher: () -> None
        :param _sfunc_container: service function container
        :type _sfunc_container: _ServiceFunctionContainer
        :param _attr_adder: attribute adder, which adds an attribute to a proxy
        :type _attr_adder: (str, Any) -> None
        """
        super().__init__(daemon=True)
        self._sfunc_reg_conn = _sfunc_reg_conn
        self._conn_flusher = _conn_flusher
        self._sfunc_container = _sfunc_container
        self._attr_adder = _attr_adder

        self._added_functions = list()

    def run(self) -> None:
        """Runs the worker"""
        while safe_transmit()(self._check_connection) is not None:
            continue

    def _check_connection(self):
        if self._sfunc_reg_conn.closed:
            return None
        if self._sfunc_reg_conn.poll():
            self._conn_flusher()
            for f_name, evaluator in self._sfunc_container._sfuncs.items():
                if f_name not in self._added_functions:
                    self._added_functions.append(f_name)
                    self._attr_adder(f_name, evaluator)
        return True


class ServiceFunctionReceiver:
    """
    Handles callbacks for instantiating service functions of service proxies

    Service process sends registered service functions via Pipe

    Processing generates service function containers for accessing underlying service function on the client side

    Processing is invoked by workers that monitor pipes between the registry in the service process and the receiver in
    the main process
    """

    KEY_CONN = "Connection"
    """Key for connection in container storage dictionary"""

    KEY_CONT = "Container"
    """Key for container in container storage dictionary"""

    service_containers = dict()
    """
    Service container storage
    
    type: Dict[str, Dict[str, Union[multiprocessing.connection.Connection, _ServiceFunctionContainer]]]
    """

    workers: Dict[str, _ServiceFunctionConnectionWorker] = dict()
    """Service function connection worker storage"""

    @classmethod
    def register_service(cls, service_proxy, service_conn) -> None:
        """
        Register service with receiver

        A service process should be registered before being deployed, since the receiver must be ready to handle
        service function callbacks during service process activity

        :param service_proxy: service proxy instance
        :param service_conn: service function callback connection; receiver side
        :type service_conn: multiprocessing.connection.Connection
        :return: None
        """
        service_name = service_proxy.process_name()
        if service_name in cls.service_containers.keys():
            raise AttributeError(f"Service {service_name} has already been registered")
        cls.service_containers[service_name] = {cls.KEY_CONN: service_conn,
                                                cls.KEY_CONT: _ServiceFunctionContainer()}

        # Spawn a worker to handle service function registration during internal service routines
        service_name = service_proxy.process_name()
        if service_name not in cls.service_containers.keys():
            raise AttributeError(f"Service {service_name} has not been registered")

        _flush_connection = cls._flush_connection
        __setattr__ = service_proxy.__setattr__

        def _flusher():
            _flush_connection(service_name)

        def _attr_adder(name, val):
            __setattr__(name, val)

        worker = _ServiceFunctionConnectionWorker(service_name,
                                                  cls.service_containers[service_name][cls.KEY_CONN],
                                                  _flusher,
                                                  cls.service_containers[service_name][cls.KEY_CONT],
                                                  _attr_adder)
        worker.start()
        cls.workers[service_name] = worker

    @classmethod
    def _flush_connection(cls, service_name: str) -> None:
        """
        Process all pending service function registrations in the Pipe of a service process

        :param service_name: name of service process
        :type service_name: str
        :return: None
        """
        conn = cls.service_containers[service_name][cls.KEY_CONN]

        while conn.poll():
            msg = conn.recv()  # ServiceFunctionConnectionMessage
            process_name, function_name, evaluator = msg()
            if process_name != service_name:
                print(f"Incorrect pipe usage {process_name} -> {service_name}. Rejecting")
                continue
            cls.service_containers[service_name][cls.KEY_CONT]._register_function(function_name, evaluator)
