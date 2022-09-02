.. _overview:

Overview
---------

Many simulation libraries and frameworks are stateful, which
complicates, if not prevents, multiple instances of their deployment in a common memory space.
SimService exists to support creating, controlling and integrating simulation instances
as interactive Python objects, with a particular emphasis on simulators that integrate
dynamical sytems in time.
SimService provides the infrastructure to easily wrap simulations in separate processes
and interact with them via a dynamic message-passing interface in a server-client architecture.

At its core, SimService uses information provided in a service implementation to automatically
create a server-side process in which a simulation is launched, and a client-side proxy
for interactive simulation execution, management and data throughput.
End-users of a SimService implementation can create multiple instances of a simulation
using client-side commands, destroy simulation instances at any time, and launch services
provided by different implementations from the same memory space.
SimService also provides mechanisms by which an end-user or implementation can
dynamically add methods to the interface of a proxy based on server-side instructions.
SimService provides this capability via the `service function`, which allows
customization of a proxy object interface according to the model and simulation
specification executed in its corresponding server-side process.
Implementations and end-users alike can add methods to a proxy for creating additional, custom
interface features, whether to issue server-side instructions via client-side commands,
access and manipulate server-side data, or otherwise.
