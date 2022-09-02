.. _implementation:

Implementation
---------------

Implementing a simulation service using infrastructure provided by SimService requires providing two
basic implementations,

1. :class:`PySimService <simservice.PySimService.PySimService>`: a class that performs server-side simulation
   launching, execution and control
2. :class:`TypeProcessWrap <simservice.service_wraps.TypeProcessWrap>`: a light class that defines information for
   generating a server-side process and client-side proxy for a
   :class:`PySimService <simservice.PySimService.PySimService>` implementation.

A :class:`PySimService <simservice.PySimService.PySimService>` implementation defines the controlling object
of a simulation. When a service is requested, SimService launches a
:class:`PySimService <simservice.PySimService.PySimService>`-derived object in its own process.
The :class:`PySimService <simservice.PySimService.PySimService>`-derived object is responsible
for accomplishing all simulation initialization, execution and management according to a pre-defined
SimService simulation scheme,

* ``run``: start the underlying process
* ``init``: do simulation initialization
* ``start``: do simulation startup
* ``step``: integrate the simulation in time
* ``finish``: conclude the simulation
* ``stop``: stop the simulation, as if interrupted

Implementations are free to implement whichever interface features are relevant to the underlying service.
Interface features are implemented by overriding :class:`PySimService <simservice.PySimService.PySimService>`
methods that correspond to interface methods, with the convention that the implementation provides a definition
for a corresponding interface method by overriding a :class:`PySimService <simservice.PySimService.PySimService>`
method with the same name and a prefix ``_`` (*e.g.*, instructions for ``run`` are provided by overriding ``_run``).
Client-side proxies have the same interface, and each method, when called by the client, forwards the request
to the corresponding method of the same name on the
:class:`PySimService <simservice.PySimService.PySimService>`-derived object through a MPI.

An implementation of the :class:`PySimService <simservice.PySimService.PySimService>` interface is demonstrated
in the following example, which also stores service-specific information.
Implementations are free to customize a :class:`PySimService <simservice.PySimService.PySimService>`
implementation according to the target simulation, and SimService automatically creates proxy interface methods
that reflect the interface of the :class:`PySimService <simservice.PySimService.PySimService>` implementation
(*i.e.*, any method on a :class:`PySimService <simservice.PySimService.PySimService>`-derived object will
have a corresponding method of the same signature on its proxies). Care must be taken in this regard in that
data is passed across the server-client barrier via serialization, and so implementations of
:class:`PySimService <simservice.PySimService.PySimService>` should only define methods requiring data that
supports serialization.

.. code-block:: python

    """
    MySimService.py
    """
    from simservice.PySimService import PySimService

    class MySimService(PySimService):

        def __init__(self, output_path: str):
            super().__init__()

            self.output_path = output_path
            """Path where this simulation saves data"""

        def _run(self) -> None:
            """
            Called by run; all prep for the underlying simulation is complete after this call!
            """

        def _init(self) -> bool:
            """
            Called by init; initialize underlying simulation

            :return: True if started; False if further start calls are required
            """

        def _start(self) -> bool:
            """
            Called by start; after simulation and before stepping

            Should set self.beginning_step to first first step of current_step counter

            :return: True if started; False if further start calls are required
            """

        def _step(self) -> bool:
            """
            Called by step; execute a step of the underlying simulation

            :return: True if successful, False if something failed
            """

        def _finish(self) -> None:
            """
            Called by finish; execute underlying simulation finish
            """

        def _stop(self, terminate_sim: bool = True) -> None:
            """
            Called by stop; execute underlying simulation stop

            :param terminate_sim: Terminates simulation if True
            """

Implementations of :class:`TypeProcessWrap <simservice.service_wraps.TypeProcessWrap>` provide SimService with
the necessary information to generate services and proxies on request by the end-user.
A :class:`TypeProcessWrap <simservice.service_wraps.TypeProcessWrap>` implementation must be registered with
a :ref:`manager <simservice.managers>`, which managers a registry of available and running services,
using a unique name before the first service request by the end-user.
At minimum, a :class:`TypeProcessWrap <simservice.service_wraps.TypeProcessWrap>` implementation for a service
must define the class that implements the :class:`PySimService <simservice.PySimService.PySimService>` interface
for the service. This definition can be accomplished by overriding the class attribute ``_process_cls``.
Additionally, a :class:`PySimService <simservice.PySimService.PySimService>` implementation can also define
properties on the underlying :class:`PySimService <simservice.PySimService.PySimService>` implementation
to make available as properties of the same names on it proxies. Defining properties to make available on proxies
is accomplished by overriding the :class:`TypeProcessWrap <simservice.service_wraps.TypeProcessWrap>` class
attribute ``_prop_names`` with a list of strings, where each string is the name of a property to make available.
Properties must be defined on the :class:`PySimService <simservice.PySimService.PySimService>` implementation, and
MPI-based rules apply.

The following example demonstrates defining a :class:`TypeProcessWrap <simservice.service_wraps.TypeProcessWrap>`
implementation and service factory method,

.. code-block:: python

    """
    MySimServiceFactory.py
    """
    from simservice.managers import ServiceManagerLocal
    from simservice.service_wraps import TypeProcessWrap
    from simservice.service_factory import process_factory
    from MySimService import MySimService

    SERVICE_NAME = "MySimService"

    class MySimServiceWrap(TypeProcessWrap):
        _process_cls = MySimService

    ServiceManagerLocal.register_service(SERVICE_NAME, MySimServiceWrap)

    def my_simservice(*args, **kwargs):
        return process_factory(SERVICE_NAME, *args, **kwargs)


End-users can then safely create services and retrieve proxies to them for interactive execution,

.. code-block:: python

    """
    MySimServiceUserScript.py
    """
    from MySimServiceFactory import my_simservice
    # Declare the location of simulation data output (specific to service)
    output_path = 'my_service_output.csv'
    # Launch a service and get a proxy to it
    my_simservice_proxy = my_simservice(output_path)
    # Start the underlying service
    my_simservice_proxy.run()
    # Do service initialization
    my_simservice_proxy.init()
    # Do service startup
    my_simservice_proxy.start()
    # Integrate the service in simulation time
    [my_simservice_proxy.step() for _ in range(100)]
    # Do service finalization
    my_simservice_proxy.finish()
