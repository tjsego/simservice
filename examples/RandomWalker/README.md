# Example: Random Walker

## Overview

This example demonstrates implementing and deploying a SimService interface implementation for a 
simulator of a one-dimensional random walker. 

## Walkthrough

### RandomWalker.py

_RandomWalker.py_ defines a simulator of a one-dimensional random walker. 
The simulator is designed to be imported into other Python code and used through the following methods:

* `step`: advance the simulator one step in simulation time
* `get_pos`: get the current position
* `set_pos`: set the current position

These methods allow applications like the following:

```python
import RandomWalker
# Simulate for 100 steps
for _ in range(100):
    RandomWalker.step()
    # Impose periodic boundary conditions on a domain [-1, 1]
    pos = RandomWalker.get_pos()
    if pos < -1.0:
        RandomWalker.set_pos(pos + 2.0)
    elif pos > 1.0:
        RandomWalker.set_pos(pos - 2.0)
```

The `RandomWalker` implementation poses a challenge to simultaneously executing multiple simulations. 
_RandomWalker.py_ stores the current position of the walker as a module-level variable (_i.e._, `pos`), 
which prevents creating multiple simulators in the same calling process.

`RandomWalker` can provide a SimService interface implementation that delivers all module methods 
but for multiple instances of the simulator, each of which operates in its own process and thus 
can be simultaneously orchestrated the same calling process. 

### RandomWalkerService.py

The core definition of the `RandomWalker` SimService interface implementation (and of any implementation) 
is an implementation of the `PySimService` class, as defined in _RandomWalkerService.py_. 
The main object of any simulation service is an instance of a 
`PySimService` implementation. Whenever requested in a calling process, 
SimService creates an instance of a `PySimService` implementation, 
copies to its own process, and then returns a proxy that facilitates message passing to and from 
the `PySimService` implementation instance _as if_ it were the actual instance. 

`RandomWalkerService` implements all requisite `PySimService` interface methods
(_i.e._, `_run`, `_init`, `_start`, `_step`, and `_finish`)
as appropriate to the `RandomWalker` simulator. 
Note that `RandomWalkerService` does not perform any special handling of collisions with 
other instances of the `RandomWalker` simulator because it can safely assume that it is the 
only user of the `RandomWalker` module in its process. 

`RandomWalkerService` also defines the methods `get_pos` and `set_pos`, which 
only call the `RandomWalker` methods of the same name. 
SimService detects these methods on the `RandomWalkerService` class definition and makes them available 
on simulation service proxies, therefore making the underlying module methods available for each 
simulation service. 
Note that `RandomWalkerService` supports optionally specifying an initial position but 
stores this data as an attribute and implements it in its definition of `_init`. 
This procedure handles the process of simulation service construction, 
where a `PySimService` implementation instance is instantiated and then copied into its own process. 
Each implementation instance does not have access to its own memory until a user first calls `run` on 
its proxy (which corresponds to `PySimService._run`), 
after which subsequent calls to proxy `init` (corresponding to `PySimService._init`) and 
`start` (corresponding to `PySimService._start`) by the user are executed in isolated memory. 

### RandomWalkerFactory.py

Each SimService interface implementation must be registered before it is available for creating 
simulation services. 
As shown in _RandomWalkerFactory.py_, registering an implementation mostly requires specifying 
boilerplate code, along with specifying a name for the registered service that is unique among all 
registered services. 
_RandomWalkerFactory.py_ also specifies the factory function `random_walker_simservice`, 
which is the factory method that allows a user to create one `RandomWalker` simulation service instance 
per call. 
`random_walker_simservice` only forwards constructor arguments for `RandomWalkerService` along with 
the unique name of the registered `RandomWalker` interface implementation to the 
SimService function `process_factory`, which is a generic function that creates a new simulation service 
instance by registered name and returns a proxy to it. 

### RandomWalkerUser.py

With the `random_walker_simservice` function available in _RandomWalkerFactory.py_, 
a user can arbitrarily create `RandomWalker` simulation services in the same process and 
orchestrate their execution using both SimService- and RandomWalker-specific methods. 
_RandomWalkerUser.py_ demonstrates a simple use case, where multiple simulators are 
simultaneously instantiated, started, and executed:

```python
from RandomWalkerFactory import random_walker_simservice
# Create ten simulators
proxies = [random_walker_simservice() for _ in range(10)]
# Do startup
for proxy in proxies:
    proxy.run()
    proxy.init()
    proxy.start()
# Simulate for 100 steps
for _ in range(100):
    for proxy in proxies:
        proxy.step()
        # Impose periodic boundary conditions on a domain [-1, 1]
        pos = proxy.get_pos()
        if pos < -1.0:
            proxy.set_pos(pos + 2.0)
        elif pos > 1.0:
            proxy.set_pos(pos - 2.0)
```
