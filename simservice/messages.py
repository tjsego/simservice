"""
Defines messages and inter-process message-passing structures
"""
import logging
from multiprocessing.connection import Pipe
from threading import Thread
from typing import Any, Callable, Tuple


logger = logging.getLogger(__name__)


class Functor:
    """A callable object"""
    def __call__(self, *args, **kwargs):
        pass


class ConnectionMessage:
    """
    Standard message class for function calling between processes via a Pipe
    """

    TERMINATOR = "ConnectionMessageTerminator"
    """Signal code to terminate connection"""

    def __init__(self, _command, *args, **kwargs):
        """
        :param _command: command name
        :type _command: str or None
        :param args: command positional arguments
        :type args: tuple
        :param kwargs: command keyword arguments
        :type kwargs: dict
        """
        self.command = _command
        self.args = args
        self.kwargs = kwargs

    def __call__(self, _functor: Functor) -> Any:
        """
        :param _functor: object with attribute *self.command*
        :type _functor: Functor
        :return: evaluation return of *self.command* on *_functor* with stored arguments
        :rtype: Any
        """
        if self.command is None:
            return _functor(*self.args, **self.kwargs)
        return getattr(_functor, self.command)(*self.args, **self.kwargs)

    @staticmethod
    def terminator():
        """
        :return: standard message to predicate connection termination
        :rtype: ConnectionMessage
        """
        return ConnectionMessage(ConnectionMessage.TERMINATOR)

    @property
    def is_terminator(self) -> bool:
        """
        :return: True if this is a terminator message
        :rtype: bool
        """
        return self.command == self.TERMINATOR


connection_terminator = ConnectionMessage(ConnectionMessage.TERMINATOR)
"""A connection terminator message"""


def dispatch_transmit(conn, _cmd, *args, **kwargs) -> Any:
    """
    Generic communication protocol: dispatcher side

    :param conn: dispatcher-worker connection, dispatcher side
    :type conn: multiprocessing.connection.Connection
    :param _cmd: function name
    :type _cmd: str or None
    :param args: function positional arguments
    :type args: tuple
    :param kwargs: function keyword arguments
    :type kwargs: dict
    :return: function return value
    :rtype: Any
    """
    msg = ConnectionMessage(_cmd, *args, **kwargs)
    conn.send(msg)
    val = conn.recv()
    return val


def dispatch_terminate(conn) -> None:
    """
    Generic communication protocol: terminate worker side

    :param conn: dispatcher-worker connection, dispatcher side
    :type conn: multiprocessing.connection.Connection
    :return: None
    """
    conn.send(connection_terminator)
    conn.recv()


def worker_transmit(conn, func) -> None:
    """
    Generic communication protocol: worker side

    Blocks until routine is terminated by dispatcher

    :param conn: dispatcher-worker connection, worker side
    :type conn: multiprocessing.connection.Connection
    :param func: functor with supporting evaluation by ConnectionMessage
    :type func: Functor
    :return: None
    """
    while True:
        msg: ConnectionMessage = conn.recv()
        if msg.is_terminator:
            # Send acknowledgment of termination before returning
            conn.send(None)
            return
        else:
            # Call functor with arguments in message
            val = msg(func)
            conn.send(val)


def safe_transmit(conn=None) -> Callable:
    """
    Wrap to do communication protocol with safe handling of common exceptions

    :param conn: connection
    :type conn: multiprocessing.connection.Connection or None; default None
    :return: function wrapper
    """
    def wrapper(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BrokenPipeError:
            if conn is not None:
                logger.warning(f"Pipe has been broken: {conn}")
            return None
        except EOFError:
            if conn is not None:
                logger.warning(f"Pipe has been closed: {conn}")
            return None
    return wrapper


class RemoteFunctionEvaluator:
    """
    Safe way to evaluate a function in a different process
    """
    def __init__(self, conn, func=None):
        """
        :param conn: RemoteFunctionEvaluator-RemoteFunctionWorker connection, RemoteFunctionEvaluator side
        :type conn: multiprocessing.connection.Connection
        :param func: function to evaluate; optional
        :type func: Callable or None
        """
        self.__conn = conn
        if func is not None:
            self.__name__ = func.__name__
        else:
            self.__name__ = f"RemoteFunctionEvaluator_{conn.__name__}"

    def __call__(self, *args, **kwargs):
        return safe_transmit(self.__conn)(dispatch_transmit, self.__conn, None, *args, **kwargs)


class ServiceFunctionConnectionMessage:
    """
    Standard message class for service function callbacks with a RemoteFunctionEvaluator - RemoteFunctionWorker pair
    """
    def __init__(self, service_name: str, function_name: str, evaluator: RemoteFunctionEvaluator):
        """
        :param service_name: service name
        :type service_name: str
        :param function_name: function name
        :type function_name: str
        :param evaluator: evaluator
        :type evaluator: RemoteFunctionEvaluator
        """
        self.service_name = service_name
        self.function_name = function_name
        self.evaluator = evaluator

    def __call__(self):
        return self.service_name, self.function_name, self.evaluator


class RemoteFunctionWorker(Thread):
    """
    Safe way to send function evaluations to a different process

    Note: this is safer than deriving from multiprocessing.Process, since potential applications include
    instantiation during bootstrap phase of parent processes
    """
    def __init__(self, conn, func, daemon: bool = False):
        """
        :param conn: RemoteFunctionEvaluator-RemoteFunctionWorker connection, RemoteFunctionWorker side
        :type conn: multiprocessing.connection.Connection
        :param func: function to evaluate
        :type func: Callable
        :param daemon: daemon argument to base Thread class
        :type daemon: bool
        """
        super().__init__(daemon=daemon)
        self.__conn = conn
        self.__func = func

    def run(self) -> None:
        """Runs the thread"""
        safe_transmit(self.__conn)(worker_transmit, self.__conn, self.__func)


def remote_function_factory(_func, daemon: bool = False) -> Tuple[RemoteFunctionEvaluator, RemoteFunctionWorker]:
    """
    Generate a pipe to evaluate a function in a different process

    Should be generated in the process that defines the function, from which the evaluator can be piped elsewhere

    Safe so long as the function and its returned data can be serialized

    :param _func: function
    :type _func: Callable
    :param daemon: daemon argument to RemoteFunctionWorker instance
    :type daemon: bool
    :return: evaluator-worker pair
    :rtype: Tuple[RemoteFunctionEvaluator, RemoteFunctionWorker]
    """
    e_conn, w_conn = Pipe()
    evaluator = RemoteFunctionEvaluator(e_conn, _func)
    worker = RemoteFunctionWorker(w_conn, _func, daemon=daemon)
    worker.start()
    return evaluator, worker
