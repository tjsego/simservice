from simservice.PySimService import PySimService
from simservice import service_function
import RandomWalker


class RandomWalkerService(PySimService):

    def __init__(self, init_pos: float = 0.0):
        super().__init__(sim_name='RandomWalker')

        self._init_pos = init_pos

    def _run(self) -> None:
        service_function(self.get_pos)
        service_function(self.set_pos)

    def _init(self) -> bool:
        RandomWalker.set_pos(self._init_pos)
        return True

    def _start(self) -> bool:
        return True

    def _step(self) -> bool:
        RandomWalker.step()
        return True

    def _finish(self) -> None:
        pass

    def get_pos(self):
        return RandomWalker.get_pos()

    def set_pos(self, pos: float):
        RandomWalker.set_pos(pos)
