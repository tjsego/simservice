"""
Defines service wraps
"""
import functools
from inspect import getmembers, isfunction
import logging
from multiprocessing import Pipe

from .messages import dispatch_terminate, dispatch_transmit
from .service_containers import ProcessContainer


logger = logging.getLogger(__name__)


def proxy_function_factory(_cmd: str, _conn) -> functools.partial:
    """
    Service proxy dispatcher function factory

    Generated function goes on client proxy wrap and dispatches commands to service
    :class:`ProcessContainer <simservice.service_containers.ProcessContainer>` instance

    :param _cmd: function name defined on server-side service wrap
    :type _cmd: str
    :param _conn: manager-process connection, manager side
    :type _conn: multiprocessing.connection.Connection
    :return: serial-safe dispatch transmiter
    :rtype: functools.partial
    """
    dispatch_transmit_conn = functools.partial(dispatch_transmit, _conn)
    return functools.partial(dispatch_transmit_conn, _cmd)


def proxy_property_accessor_factory(_name: str, _conn):
    """
    Service proxy dispatcher property factory

    :param _name: property name
    :type _name: str
    :param _conn: manager-process connection, manager side
    :type _conn: multiprocessing.connection.Connection
    :return: property getter, setter
    """
    def _fget():
        return proxy_function_factory('__getattribute__', _conn)(_name)

    def _fset(_val):
        return proxy_function_factory('__setattr__', _conn)(_name, _val)

    return _fget, _fset


class TypeProcessWrap:
    """
    Process wrap base class

    Client service proxies are generated from this wrap

    Service implementations should derive a wrap from this and register it with an appropriate service manager

    Service wraps with method and property names that collide with those defined on this class will be ignored when
    generating a client-side proxy class
    """

    _process_cls = None
    """
    Class defining the underlying simulation service
    
    Implementations must override this attribute
    """

    _prop_names = None
    """
    Container for presenting properties defined on the underlying simulation service class on the client side
    """

    def __init__(self, _return_conn,
                 *args, **kwargs):
        assert self._process_cls is not None

        logger.info(f"Launching service {self._process_cls}...")

        manager_conn, container_conn = Pipe()

        # Gather functions and properties to ensure that they aren't overwritten during collisions with process class

        # Absorb process class functions
        # Functions with a name that collides with this class are ignored
        [setattr(self, f, proxy_function_factory(f, manager_conn)) for f in self._function_names()]

        # Absorb process class properties
        # Properties with a name that collides with this class are ignored
        for p in self._property_names():
            fget, fset = proxy_property_accessor_factory(p, manager_conn)
            setattr(self, f"get_{p}", fget)
            setattr(self, f"set_{p}", fset)

        # Set up process container
        self._conn = manager_conn
        self._container = ProcessContainer(container_conn,
                                           self._process_cls,
                                           *args, **kwargs)
        self._container.start()
        # Wait for launch confirmation with process id and service function connection
        self._process_name, sfunc_receiver_conn = self._conn.recv()

        logger.info(f"Service launched: {self._process_cls}")

        _return_conn.send((self._process_name, self._conn, sfunc_receiver_conn))

    def __del__(self):
        self.close()

    def close(self):
        """Closes the proxy"""
        if not self._conn.closed:
            # Send terminator and wait for container response before going to garbage
            logger.info(f"Closing service {self._process_cls}...")
            dispatch_terminate(self._conn)
            self._container.terminate()
            self._conn.close()
            logger.info(f"Service closed: {self._process_cls}")

    @classmethod
    def _native_names(cls):
        sf = [f[0] for f in getmembers(cls, predicate=isfunction)]
        sp = [p for p in dir(cls) if isinstance(getattr(cls, p), property)]
        return dir(cls) + sf + sp

    @classmethod
    def _function_names(cls):
        return [f[0] for f in getmembers(cls._process_cls, predicate=isfunction) if f not in cls._native_names()]

    @classmethod
    def _property_names(cls):
        if cls._prop_names is None:
            cls._prop_names = [p for p in dir(cls._process_cls) if isinstance(getattr(cls._process_cls, p), property)
                               if p not in cls._native_names()]
        return cls._prop_names

    def process_name(self) -> str:
        """
        Reserved function for uniquely identifying a service process

        Do not override

        :return: unique process name
        :rtype: str
        """
        return self._process_name
