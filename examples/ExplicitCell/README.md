# Example: Explicit Cell

## Overview

This example demonstrates building a simulation of single cell motility with explicit 
subcellular detail by constructing simulation services with 
[CompuCell3D](https://github.com/CompuCell3D/CompuCell3D) (cell motility) and 
[Tissue Forge](https://github.com/tissue-forge/tissue-forge/tree/main) (subcellular dynamics) 
and orchestrating them.

CompuCell3D (CC3D) v4.4.0+ provides a SimService interface implementation as the backend of its Python API. 
This example demonstrates how to customize the interface of CC3D simulation services using service functions. 

Tissue Forge (TF) v0.2.0 does not provide a SimService interface implementation. 
This example demonstrates how to build a SimService interface implementation for an advanced simulator. 

### Conceptual Requirements

This example assumes that the reader has a working familiarity with CC3D and TF. 
Refer to the online documentation for 
[CC3D](https://pythonscriptingmanual.readthedocs.io/en/latest/) and 
[TF](https://tissue-forge-documentation.readthedocs.io/en/latest/) for more information about each simulator. 

### Runtime Requirements

This example requires the following packages to execute, which are available via conda:

* Tissue Forge v0.2.0 (package: [tissue-forge](https://anaconda.org/tissue-forge/tissue-forge); channel: tissue-forge)
* CompuCell3D v4.4.0 (package: [cc3d](https://anaconda.org/compucell3d/cc3d); channel: compucell3d)

From a terminal, these packages can be installed into a new conda environment named `explicit_cell_env` 
with the following command:

```bash
conda create -n explicit_cell_env -c conda-forge -c compucell3d -c tissue-forge cc3d=4.4.0 tissue-forge=0.2.0
```

## Walkthrough

The basic premise of constructing this example is as follows:

1. A TF simulation service simulates a moving cell boundary and fluid dynamics inside the cell as it moves.
   It provides an interface to upload a new mask and integrates subcellular dynamics to interpolate the cell 
   boundary according to the new mask.
2. A CC3D simulation service simulates single cell motility. 
   It provides an interface to retrieve a mask that identifies which locations are occupied by the cell.
3. A user orchestrates an instance of the CC3D and TF simulation services such that CC3D generates new 
   cellular configurations that drive TF subcellular dynamics.

Here a _mask_ is a two-dimensional array of integers that correspond to the occupancy of locations in 
a two-dimensional domain. Each integer uniquely identifies a cell such that a mask describes the 
shape of each cell in the domain, where an integer `0` corresponds to the medium. 
The mask is the common data of the two simulation services. 
A CC3D simulation produces new masks from simulating cell motility, 
and a TF simulation service consumes those masks to simulate subcellular dynamics during cell motility. 

### Subcellular Dynamics Service

The TF subcellular dynamics simulation service assumes that a cell consists of a simply connected 
two-dimensional domain filled with a fluid and with an impenetrable boundary that moves from 
one configuration to another. 
The TF simulation service represents the fluid with particles using dissipative particle dynamics, 
and represents the boundary as particles that are packed sufficiently close to approximate a surface. 
The fluid particles collide with each other and the boundary. 
When given a new mask, the TF simulation service calculates the position of each boundary particle 
according to the next mask and assigns a constant force to each particle so that it arrives at its 
next position after a given number of simulation steps. 

Since TF does not provide a SimService interface implementation, one must be constructed. 
In general, TF requires one module function call (`tissue_forge.init`) to initialize the simulator, 
which supports a number of optional arguments like the size and discretization of the simulation. 
This particular application also supports a number of options in deployment, such as 
the number of TF integration steps per time step and 
the number of boundary particles per cell mask edge. 
The TF SimService interface implementation is designed to support both launching TF and using 
TF to accomplish the goals of this simulation service. 

_tf_simservice/TissueForgeSimService.py_ defines `TissueForgeSimService`, 
the TF SimService interface implementation for this application. 
The `TissueForgeSimService` constructor takes the following arguments:

* `dim`: the dimensions of the TF simulation domain. 
* `cells`: the number of TF domain cells per dimension, for spatial decomposition. 
* `per_dim`: the number of TF space per unit of distance in the mask. 
* `num_steps`: the number of TF integration steps per time step. 
* `num_refinements`: the number of mask edge refinements for determining boundary particle number and positions. 
* `render_substepping`: optional tuple specifying the period and output directory for rendering to file. 

The TF SimService interface implementation stores arguments for initializing TF (`dim` and `cells`), 
for when the simulation service is launched by the user. 
Settings for customizing the TF simulation service (`per_dim`, `num_steps`, and `num_refinements`) are 
stored by the TF SimService interface implementation for later use when operating the simulation service. 
The simulation service generates and stores coordinates (`coords_x` and `coords_y`)
that correspond to the coordinates of masks that it expects to receive, 
which are determined from the constructor arguments `dim` and `per_dim`. 
The simulation service stores the mask by which the simulation is currently moving cell boundaries (`next_mask`). 
The simulation service keeps a registry of TF particles that correspond to the fluid and boundary of 
each cell being simulated, where a cell is uniquely identified by an integer label that corresponds to 
its locations in masks passed to the service. 

Startup of this TF simulation service is summarized as follows:

* `run`: Initialize the underlying TF simulation.
* `init`: Perform any auxiliary rendering setup. 
* `start`: Initialize particle types and bind inter-particle interactions. 

When stepping this TF simulation service (_i.e._, by calling `step` on its proxy, 
which corresponds to `TissueForgeSimService._step`), 
the simulation service first checks whether a new mask has been passed and returns if not. 
For each cell, the service retrieves the current and next positions of each boundary particle. 
Next boundary particle positions are determined by calculating the edges of the next mask and 
evenly discretizing those edges by length, as defined in `generate_outline`, 
and then mapping each particle to the nearest next position that maintains the current boundary topology, 
as defined in `identify_outline_partners` and `interp_changed`. 
The displacement over the step for each boundary particle is calculated and imposed by applying a constant force. 
After integrating the TF simulation to the next mask, all boundary particles are regenerated. 

The TF SimService interface implementation provides a number of custom methods to integrate 
this simulation service, each of which is defined on the `TissueForgeSimService` class definition 
for availability on simulation service proxies: 

* `TissueForgeSimService.set_next_mask`: Sets the next mask. 
   Expects a two-dimensional NumPy integer array. 
* `TissueForgeSimService.add_domain`: Adds a cell. 
   A boundary is automatically constructed and filled with uniformly distributed fluid particles. 
   Expects an integer to identify the cell and the current mask. 
* `TissueForgeSimService.rem_domain`: Removes a cell. 
   Expects the integer that identifies the cell. 
* `TissueForgeSimService.module_command`: Calls a function on the underlying TF Python module. 
   Excepts the name of the function, and optionally the names of any submodules and position and keyword arguments. 
   For example, `TissueForgeSimService.module_command('init', dim=[10.0, 10.0, 10.0])`. 
* `TissueForgeSimService.screenshot`: Renders a screenshot to file. 
   Expects the absolute path of the file. 
* `TissueForgeSimService.equilibrate`: Equilibrates the simulation. 
   Optionally takes as argument the number of simulation steps to execute. 
   Runs the simulation without moving the boundaries, to allow fluid particles to equilibrate. 

The TF SimService interface implementation is registered with SimService in 
_tf_simservice/TissueForgeSimServiceFactory.py_. 
The script also defines a factory function `tissue_forge_simservice`, 
which is the main user entry point for constructing this simulation service. 
_tf_simservice/__init__.py_ formalizes this entry point by importing it 
such that a user can retrieve the factory function with code like 
`from tf_simservice import tissue_forge_simservice`. 

### Cell Motility Service

In general, CC3D supports using modeling with both built-in and user-custom features 
through _Plugins_ and _Steppables_. 
Plugins are built-in features that provide models for properties and processes like 
cell volume, intercellular adhesion, and chemotaxis, that perform operations during cellular dynamics. 
Steppables are built-in features that provide additional capabilities but operate 
between cellular dynamics integration steps (_e.g._, mitosis). 
CC3D supports custom code by providing a Python-based Steppable class that 
custom code can particularize to inject custom models into a simulation. 

CC3D provides a SimService interface implementation such that any CC3D simulation 
specified through the CC3D Python API can be executed as a simulation service. 
Furthermore, SimService service functions allow customization of a simulation service interface 
during runtime, meaning that a CC3D simulation can specify additional interface features that 
are particular to the simulation, beyond those customizations already provided by CC3D. 
Hence, this simulation service has three layers to its interface: 

1. Interface features particular to SimService, 
2. Interface features particular to CC3D, and 
3. Interface features particular to a CC3D simulation.

_cc3d_sim.py_ contains all specification for the CC3D simulation service. 
Every CC3D simulation service has interface methods to register 
built-in plugins and steppables (`register_specs`) 
and custom steppables (`register_steppable`). 
In `new_sim`, a CC3D simulation service is created with typical CC3D plugins 
for a declaring cell types, a cell volume constraint, adhesion, and a 
CC3D plugin called the _PixelTracker_ that maintains an updated list of all 
locations currently occupied by each cell. 

The CC3D simulation service is also launched with one custom Steppable, `InterfaceSteppable`, 
which is so named because it defines the interface for using the simulation service:

* `InterfaceSteppable.add_cell`: Adds a cell to the simulation. 
   Expects a list of locations to place the cell specified as a 2-tuple of integers. 
   Returns the unique integer identification of the cell according to CC3D. 
* `InterfaceSteppable.rem_cell`: Removes a cell. 
   Expects the integer that identifies the cell. 
* `InterfaceSteppable.cell_mask`: Returns a mask of the current simulation domain. 
   Medium sites are labeled with a `0`. 
   Cell sites are labeled with the unique integer identification of the cell according to CC3D. 

When the `start` method of a CC3D simulation service is called, the CC3D simulation service 
calls the `start` method of every registered custom Steppable. 
Hence, `InterfaceSteppable.start` calls the SimService function 
`service_function` on every interface method 
(_i.e._, `InterfaceSteppable.add_cell`, 
`InterfaceSteppable.rem_cell`, 
`InterfaceSteppable.cell_mask`) 
to make those methods available on the proxy of 
the simulation service along with all customizations already provided by the 
CC3D SimService interface implementation. 
Otherwise, startup of this simulation service it typical of any CC3D simulation service.

### Multi-simulation orchestration

_cc3d_sim.py_ also defines instantiating and orchestrating both simulation services to 
simulate cell motility with subcellular dynamics. 
The `__main__` block demonstrates typical usage of the simulation services. 

Both simulation services are launched by the function `new_sim`. 
Both simulation services construct spatial domains of the same dimensions and 
perform all startup, and the simulation service proxies generated by SimService are returned. 

The function `add_cell` coordinates adding a cell to both simulation services. 
Given locations occupied by the cell are passed to the CC3D simulation service to add a cell, 
which returns the identification integer of the cell. 
The cell identification integer and mask according to 
the CC3D simulation service are both passed to the TF simulation service to add a cell. 
After adding a cell using `add_cell`, the TF simulation is equilibrated before simulation. 

The `__main__` block calls a few auxiliary methods that set up visualization and rendering 
and are not critical to actually executing the simulation. 
The function `configure_cc3d_viz_manual` defines a procedure for configuring CC3D visualization 
through an interactive graphics pane. 
The TF simulation service method `start_substep_output` instructs the service to inject an event 
into the TF event system that saves screenshots at intermediate time steps. 

Lastly, the `__main__` block orchestrates the execution of simulation steps through the function `step`. 
The CC3D simulation service is first integrated to generate a new cellular configuration. 
A new mask is generated by the CC3D simulation service, which is passed to the 
TF simulation service. 
The TF simulation service is then integrated to simulate subcellular dynamics. 
A function `save_screenshot` is called at every simulation step, 
which instructs each simulation service to render visualization to file. 

