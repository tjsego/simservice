# SimService

<p align=center>
<img src="examples/ExplicitCell/explicit_cell_animation.gif">
<br/>
<em>
Simulation of single cell motility with subcellular dynamics using 
simulation services built with CompuCell3D and Tissue Forge. 
Gray shaded regions show a medium according to CompuCell3D. 
Tissue Forge particles represent subcellular components, where blue particles are segments of the cell membrane, 
and red particles are parcels of fluid. 
<br/>
This example is available in the 
<a href="examples">examples</a> directory 
<a href="examples/ExplicitCell">ExplicitCell</a>.
</em>
</p>

SimService is a library for building simulation services in Python.
SimService is lightweight, written in pure Python and designed to generate
memory-isolated, interactive proxy objects of simulations with minimal effort.
SimService is especially designed to encapsulate stateful simulations,
simulation libraries and frameworks for usage in general Python environments
as interactive objects that can be integrated into larger computational workflows
and interconnected in multi-method models and simulations. In support of simulation
frameworks, SimService provides support for customizing the interface of service
proxies at multiple levels of an underlying service, both statically in a service
implementation, as well as dynamically in the specification of a simulation.

[![PyPI version](https://badge.fury.io/py/simservice.svg)](https://badge.fury.io/py/simservice)

[![Anaconda-Server Badge](https://anaconda.org/conda-forge/simservice/badges/version.svg)](https://anaconda.org/conda-forge/simservice)

[![Documentation Status](https://readthedocs.org/projects/simservice/badge/?version=latest)](https://simservice.readthedocs.io/en/latest/?badge=latest)

## Installation

SimService is available for installation via pip: 

```bash
pip install simservice
```

SimService is also available for installation via conda:

```bash
conda install -c conda-forge simservice
```

## End-user Application Example

Suppose a module ``RandomWalker`` provides capability to simulate a one-dimensional random
walker that moves according to a uniform distribution, and also provides a SimService
implementation with additional interface features to get and set the position of a
random walker during execution. SimService supports passing any data that can be serialized
into and out of a ``RandomWalker`` simulation instance through methods that the
``RandomWalker`` module adds to the interface of its SimService implementation
[proxies](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.PySimService.PySimService) using
[service_functions](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.service_function),

```python
"""
RandomWalker.py
"""
from random import random
from simservice import service_function

pos: float = 0.0

def step():
    global pos
    pos += 2.0 * random() - 1.0

def get_pos():
    return pos

def set_pos(_val: float):
    global pos
    pos = _val

# Make the current position available on SimService proxies
service_function(get_pos)
# Make the current position settable on SimService proxies
service_function(set_pos)
```

Now suppose that the ``RandomWalker`` module provides a SimService proxy factory
``service_random_walker`` to efficiently create SimService proxy instances, where
the SimService proxy method ``step`` calls the underlying ``step`` function of
*RandomWalker.py*. An end-user of ``RandomWalker`` can use whatever functions defined
in *RandomWalker.py* are declared as 
[service_functions](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.service_function),
and with the same signature, on a proxy instance. For example, if the end-user wishes to
impose periodic boundary conditions on their ``RandomWalker`` simulation, they can use the
``get_pos`` and ``set_pos`` service functions declared in *RandomWalker.py*, which call
their underlying functions of the same name,

```python
"""
RandomWalkerUser.py
"""
from RandomWalker import service_random_walker

random_walker_proxy = service_random_walker()
random_walker_proxy.run()
random_walker_proxy.init()
random_walker_proxy.start()
for _ in range(100):
    random_walker_proxy.step()
    # Impose periodic boundary conditions on a domain [-1, 1] using service functions
    pos = random_walker_proxy.get_pos()
    if pos < -1.0:
        random_walker_proxy.set_pos(pos + 2.0)
    elif pos > 1.0:
        random_walker_proxy.set_pos(pos - 2.0)
random_walker_proxy.finish()
```

SimService [proxies](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.PySimService.PySimService) 
support serialization and so can be attached to, and executed in, separate processes, whether as single,
background processes or in batch execution. 
[PySimService](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.PySimService.PySimService)
provides a method [inside_run](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.PySimService.PySimService.inside_run)
that takes a Python function as argument, where the function defines instructions for
execution of a proxy that is passed as argument. This functionality gives end-users the
ability to prescribe execution instructions to be carried out by a
[proxy](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.PySimService.PySimService) 
when [PySimService.run](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.PySimService.PySimService.run) 
is called (*e.g.*, by a process that they define).
For example, suppose an end-user wishes to execute a batch of ``RandomWalker`` simulations
as defined above in parallel, and has defined a function ``execute_in_parallel`` that
executes each of a list of ``RandomWalker``
[proxies](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.PySimService.PySimService) 
in a separate process. The end-user can define a function ``inside_run`` that carries out their simulation on
a ``RandomWalker`` [proxy](https://simservice.readthedocs.io/en/latest/api/index.html#simservice.PySimService.PySimService) 
and set it on each instance before batch execution. After execution, references to each instance and all
underlying data are still valid and accessible,

```python
def inside_run(proxy_inst):
    """Function for parallel execution"""
    proxy_inst.init()
    proxy_inst.start()
    for _ in range(100):
        proxy_inst.step()
        # Impose periodic boundary conditions on a domain [-1, 1]
        pos = proxy_inst.get_pos()
        if pos < -1.0:
            proxy_inst.set_pos(pos + 2.0)
        elif pos > 1.0:
            proxy_inst.set_pos(pos - 2.0)
    proxy_inst.finish()

# Create a set of proxies to simulate in parallel according to instructions defined in inside_run
random_walker_proxies = []
for _ in range(10):
    rwp = service_random_walker()
    rwp.set_inside_run(inside_run)
    random_walker_proxies.append(rwp)
# Execute in parallel; SimService calls inside_run on each proxy
execute_in_parallel(random_walker_proxies)
# Calculate the mean final position
final_positions = [rwp.get_pos() for rwp in random_walker_proxies]
mean_position = sum(final_positions) / len(final_positions)
```
