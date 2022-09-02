"""
Defines the base class for simulation services
"""
from enum import Enum
from typing import Callable, Optional


class SimStatus(Enum):
    """Simulation status enum"""
    SIM_REGISTERED = 0
    SIM_LOADED = 1
    SIM_INITIALIZED = 2
    SIM_STARTED = 3
    SIM_RUNNING = 4
    SIM_STOPPED = 5
    SIM_FINISHED = 6
    SIM_FAILED = -1


class PySimService:
    """
    Client-side interface for simulation service processes
    Implementations should derive a wrap for an underlying service from this class

    Basic usage is

    .. code-block:: python

        sim = PySimService()
        sim.run()
        sim.init()
        sim.start()
        for s in range(S):
            sim.step()
        sim.finish()

    Status reporting is as follows

    - sim = PySimService()          : sim.status -> SimStatus.REGISTERED
    - sim.run()                     : sim.status -> SimStatus.SIM_LOADED
    - sim.init()                    : sim.status -> SimStatus.SIM_INITIALIZED
    - sim.start()                   : sim.status -> SimStatus.SIM_STARTED
    - sim.step()                    : sim.status -> SimStatus.SIM_RUNNING
    - sim.finish()                  : sim.status -> SimStatus.SIM_FINISHED
    - sim.stop()                    : sim.status -> SimStatus.SIM_STOPPED
    - sim.stop(terminate_sim=False) : sim.status -> SimStatus.SIM_FINISHED

    """
    def __init__(self, sim_name: str = '', *args, **kwargs):

        # Simulation details
        self._sim_name: str = sim_name
        """Name of simulation"""

        self.beginning_step: int = -1
        """First simulaton step"""

        self._current_step: int = -1
        """Current simulation step"""

        # In case of failure
        self._error_message: Optional[str] = None
        """Error message to report on demand, if any"""

        self.status: SimStatus = SimStatus.SIM_REGISTERED
        """Current serivce status"""

        self._inside_run: Callable[[PySimService], None] = self.inside_run
        """Hook for control in parallel applications"""

    @property
    def current_step(self) -> int:
        """Current simulation step"""
        return self._current_step

    @property
    def error_message(self) -> Optional[str]:
        """Error message to report on demand, if any"""
        return self._error_message

    def run(self):
        """
        Initialize underlying simulation

        All prep for the underlying simulation is complete after this call

        Returned dictionary contains

        - name: the name of the simulation
        - sim: this servce instance

        :return: name and reference of this service instance
        """

        self._run()

        self.status = SimStatus.SIM_LOADED

        self._inside_run(self)

        return {'name': self._sim_name, 'sim': self}

    @staticmethod
    def inside_run(self) -> None:
        """
        Called inside run; this supports parallel applications

        To support running a service in parallel, overload this or set it
        via :meth:`set_inside_run` with what to do when this service acts without
        further control from the calling process

        :param self: this service instance
        :type self: PySimService
        :return: None
        """

    def set_inside_run(self, _inside_run_func) -> None:
        """
        Set inside run function

        :param _inside_run_func: inside run function
        :type _inside_run_func: (PySimService) -> None
        :return: None
        """
        self._inside_run = _inside_run_func

    def set_sim_name(self, _sim_name: str) -> None:
        """
        Set simulation name after instantiation

        :param _sim_name: name of the simulation
        :type _sim_name: str
        :return: None
        """
        self._sim_name = _sim_name

    def init(self) -> bool:
        """
        Initialize underlying simulation

        :return: True if started; False if further start calls are required
        :rtype: bool
        """
        init_status: bool = self._init()

        if init_status:
            self.status = SimStatus.SIM_INITIALIZED

        return init_status

    def start(self) -> bool:
        """
        After simulation and before stepping

        :return: True if started; False if further start calls are required
        :rtype: bool
        """
        start_status: bool = self._start()

        if start_status:
            self._current_step = self.beginning_step
            self.status = SimStatus.SIM_STARTED

        return start_status

    def step(self) -> bool:
        """
        Execute a step of the underlying simulation

        :return: True if successful, False if something failed
        :rtype: bool
        """

        step_status = self._step()

        if step_status:
            self.status = SimStatus.SIM_RUNNING
            self._current_step += 1

        return step_status

    def finish(self) -> None:
        """
        Execute underlying simulation finish

        :return: None
        """
        self._finish()

        self.status = SimStatus.SIM_FINISHED

    def stop(self, terminate_sim: bool = True) -> None:
        """
        Execute underlying stop

        :param terminate_sim: Terminates simulation if True; default True
        :type terminate_sim: bool
        :return: None
        """
        self._stop(terminate_sim=terminate_sim)

        if terminate_sim:
            self.status = SimStatus.SIM_FINISHED
        else:
            self.status = SimStatus.SIM_STOPPED

    def _run(self) -> None:
        """
        Called by :meth:`run`; all prep for the underlying simulation is complete after this call!

        :return: None
        """
        raise NotImplementedError

    def _init(self) -> bool:
        """
        Called by :meth:`init`; initialize underlying simulation

        :return: True if started; False if further init calls are required
        :rtype: bool
        """
        raise NotImplementedError

    def _start(self) -> bool:
        """
        Called by :meth:`start`; after simulation and before stepping

        Should set self.beginning_step to first first step of current_step counter

        :return: True if started; False if further start calls are required
        :rtype: bool
        """
        raise NotImplementedError

    def _step(self) -> bool:
        """
        Called by :meth:`step`; execute a step of the underlying simulation

        :return: True if successful, False if something failed
        :rtype: bool
        """
        raise NotImplementedError

    def _finish(self) -> None:
        """
        Called by :meth:`finish`; execute underlying simulation finish

        :return: None
        """
        raise NotImplementedError

    def _stop(self, terminate_sim: bool = True) -> None:
        """
        Called by stop; execute underlying simulation stop

        :param terminate_sim: Terminates simulation if True; default True
        :type terminate_sim: bool
        :return: None
        """

    def steer(self) -> bool:
        """
        Execute steering; calling signal for ad-hoc changes to service and underlying simulation data

        :return: True if OK, False if something went wrong
        :rtype: bool
        """
        return True

    @property
    def profiler_report(self) -> str:
        """
        Return on-demand profiling information about simulation service

        :return: profiling information
        :rtype: str
        """
        return ""
