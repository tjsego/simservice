"""
Defines utility features
"""
from contextlib import AbstractContextManager
import multiprocessing.pool

from .service_factory import close_service


class NonDaemonicProcess(multiprocessing.Process):
    """
    A non-daemonic process
    """
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, _val):
        pass


class NonDaemonicContext(type(multiprocessing.get_context())):
    """
    A non-daemonic context
    """
    Process = NonDaemonicProcess


class NonDaemonicPool(multiprocessing.pool.Pool):
    def __init__(self, *args, **kwargs):
        kwargs['context'] = NonDaemonicContext()
        super().__init__(*args, **kwargs)


class ExecutionContext(AbstractContextManager):
    """
    A context to automate much of the mundane details of managing simple services
    """
    def __init__(self, _proxy, run: bool = True, init: bool = True, start: bool = True, finish: bool = True, close: bool = True):
        self._proxy = _proxy
        self._flag_run = run
        self._flag_init = init
        self._flag_start = start
        self._flag_finish = finish
        self._flag_close = close

    def __enter__(self):
        if self._flag_run:
            self._proxy.run()
        if self._flag_init:
            self._proxy.init()
        if self._flag_start:
            self._proxy.start()
        return super().__enter__()

    def __exit__(self, _exc_type, _exc_value, _traceback):
        if self._flag_finish:
            self._proxy.finish()
        if self._flag_close:
            close_service(self._proxy)
        return super().__exit__(_exc_type, _exc_value, _traceback)
