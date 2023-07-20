"""
Defines utility features
"""
import multiprocessing.pool


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
