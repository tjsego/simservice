from cc3d.core.simservice import service_cc3d
from cc3d.core import PyCoreSpecs as pcs
from cc3d.core.PySteppables import SteppableBasePy
from tf_simservice import tissue_forge_simservice
from tf_simservice.TissueForgeSimService import TissueForgeSimService

import numpy as np
import os
from simservice import service_function
from typing import List, Tuple


cell_type_name = 'cell'
results_dir = os.path.join(os.path.dirname(__file__), 'results')


def unique_trial_dir():
    trial_dir = None
    while trial_dir is None or os.path.isdir(trial_dir):
        trial_dir = os.path.join(results_dir, f'trial_{np.random.randint(0, int(1E9))}')
    return trial_dir


class InterfaceSteppable(SteppableBasePy):

    def start(self):
        service_function(self.add_cell)
        service_function(self.rem_cell)
        service_function(self.cell_mask)

    @property
    def type(self):
        return getattr(self.cell_type, cell_type_name)

    def add_cell(self, loc: List[Tuple[int, int]]):
        new_cell = self.new_cell(self.type)
        for x, y in loc:
            self.cell_field[x, y, 0] = new_cell
        return new_cell.id

    def rem_cell(self, cell_id: int):
        self.delete_cell(self.fetch_cell_by_id(cell_id))

    def cell_mask(self):
        result = np.zeros((self.dim.x, self.dim.y), dtype=int)
        for cell in self.cell_list:
            for ptd in self.get_cell_pixel_list(cell):
                result[ptd.pixel.x, ptd.pixel.y] = cell.id
        return result


def new_sim(dim: List[int],
            cells: List[int],
            render_substepping_per: int = None,
            render_substepping_dir: str = None):
    specs = [pcs.PottsCore(dim_x=dim[0],
                           dim_y=dim[1],
                           fluctuation_amplitude=10.0),
             pcs.PixelTrackerPlugin(),
             pcs.CellTypePlugin(cell_type_name)]

    volume_plugin = pcs.VolumePlugin()
    volume_plugin.param_new(cell_type_name, 100, 10)
    specs.append(volume_plugin)

    contact_plugin = pcs.ContactPlugin(2)
    contact_plugin.param_new(cell_type_name, 'Medium', 10)
    contact_plugin.param_new(cell_type_name, cell_type_name, 10)
    specs.append(contact_plugin)

    sim_cc3d = service_cc3d()
    sim_cc3d.register_specs(specs)
    sim_cc3d.register_steppable(InterfaceSteppable)

    sim_cc3d.run()
    sim_cc3d.init()
    sim_cc3d.start()

    render_substepping = None
    if render_substepping_per is not None and render_substepping_dir is not None:
        render_substepping = (render_substepping_per, render_substepping_dir)
    sim_tf: TissueForgeSimService = tissue_forge_simservice(dim=dim,
                                                            cells=cells,
                                                            per_dim=5,
                                                            num_steps=1000,
                                                            render_substepping=render_substepping)
    sim_tf.run()
    sim_tf.init()
    sim_tf.start()

    return sim_cc3d, sim_tf


def add_cell(sim_cc3d, sim_tf, loc: List[Tuple[int, int]]):
    cell_id = sim_cc3d.add_cell(loc)
    sim_tf.add_domain(cell_id, sim_cc3d.cell_mask())
    return cell_id


def rem_cell(sim_cc3d, sim_tf, cell_id: int):
    sim_cc3d.rem_cell(cell_id)
    sim_tf.rem_domain(cell_id)


def step(sim_cc3d, sim_tf):
    sim_cc3d.step()
    sim_tf.set_next_mask(sim_cc3d.cell_mask())
    sim_tf.step()


def get_cc3d_viz(sim_cc3d):
    viz = sim_cc3d.visualize()
    viz.set_drawing_style('2D')
    viz.cell_borders_on = False
    return viz


def configure_cc3d_viz_manual(sim_cc3d):
    viz = get_cc3d_viz(sim_cc3d)
    viz.set_drawing_style('2D')
    viz.draw(blocking=True)

    input('Press any key to continue...')
    return viz


def save_screenshot(step_num: int, trial_dir: str, sim_cc3d_viz, sim_tf):
    ss_fp_tf = os.path.join(trial_dir, f'tf_{step_num}.jpg')
    sim_tf.screenshot(filepath=ss_fp_tf)

    ss_fp_cc3d = os.path.join(trial_dir, f'cc3d_{step_num}.jpg')
    sim_cc3d_viz.draw(blocking=True)
    sim_cc3d_viz.save_img(file_path=ss_fp_cc3d, scale=4)


if __name__ == '__main__':

    _trial_dir = unique_trial_dir()
    print('Trial directory:', _trial_dir)
    os.makedirs(_trial_dir)

    _trial_substepping_dir = os.path.join(_trial_dir, 'substeps')

    _sim_cc3d, _sim_tf = new_sim(dim=[30, 30, 10],
                                 cells=[6, 6, 2],
                                 render_substepping_per=10,
                                 render_substepping_dir=_trial_substepping_dir)
    _loc = []
    for _i in range(10, 20):
        for _j in range(10, 20):
            _loc.append((_i, _j))
    _cell_id = add_cell(_sim_cc3d, _sim_tf, _loc)

    _sim_cc3d_viz = configure_cc3d_viz_manual(_sim_cc3d)

    _sim_tf.equilibrate()
    _sim_tf.start_substep_output()

    for i in range(100):
        print(f'Step {i}')
        step(_sim_cc3d, _sim_tf)
        save_screenshot(i, _trial_dir, _sim_cc3d_viz, _sim_tf)
