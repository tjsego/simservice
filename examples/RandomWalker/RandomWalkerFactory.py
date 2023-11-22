from simservice.managers import ServiceManagerLocal
from simservice.service_wraps import TypeProcessWrap
from simservice.service_factory import process_factory
from RandomWalkerService import RandomWalkerService

SERVICE_NAME = "RandomWalkerService"


class RandomWalkerServiceWrap(TypeProcessWrap):
    _process_cls = RandomWalkerService


ServiceManagerLocal.register_service(SERVICE_NAME, RandomWalkerServiceWrap)


def random_walker_simservice(*args, **kwargs):
    return process_factory(SERVICE_NAME, *args, **kwargs)
