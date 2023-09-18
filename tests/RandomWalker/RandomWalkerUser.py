from RandomWalkerFactory import random_walker_simservice
from multiprocessing import Pool
from simservice import ExecutionContext, close_service
from simservice.utils import NonDaemonicPool
from statistics import mean, stdev


def _execute(random_walker_proxy):
    with ExecutionContext(random_walker_proxy, run=False, close=False):
        for i in range(100):
            random_walker_proxy.step()
            # Impose periodic boundary conditions on a domain [-1, 1] using service functions
            pos = random_walker_proxy.get_pos()
            if pos < -1.0:
                random_walker_proxy.set_pos(pos + 2.0)
            elif pos > 1.0:
                random_walker_proxy.set_pos(pos - 2.0)
    return random_walker_proxy.get_pos()


def single_run():
    w = random_walker_simservice()
    with ExecutionContext(w):
        result = _execute(w)
    return result


def multi_run(num_insts: int = 8, num_workers: int = 8):
    rws = [random_walker_simservice() for _ in range(num_insts)]
    [w.run() for w in rws]
    with Pool(num_workers) as pool:
        result = pool.map(_execute, rws)
    [close_service(w) for w in rws]
    return result


def _run(w):
    w.run()


def multi_run_inside(num_insts: int = 8, num_workers: int = 8):
    rws = [random_walker_simservice() for _ in range(num_insts)]
    [w.set_inside_run(_execute) for w in rws]
    with Pool(num_workers) as pool:
        pool.map(_run, rws)
    result = [w.get_pos() for w in rws]
    [close_service(w) for w in rws]
    return result


def _inst_execute(_):
    w = random_walker_simservice()
    w.run()
    result = _execute(w)
    close_service(w)
    return result


def multi_run_nondaemonic(num_insts: int = 8, num_workers: int = 8):
    with NonDaemonicPool(num_workers) as pool:
        result = pool.map(_inst_execute, [None] * num_insts)
    return result


if __name__ == '__main__':
    print('==========')
    print('Single run')
    print('==========')
    print('Final position:', single_run())

    print('=========')
    print('Multi run')
    print('=========')
    multi_run_results = multi_run()
    print('Final position mean    :', mean(multi_run_results))
    print('Final position st. dev.:', stdev(multi_run_results))

    print('==================')
    print('Multi run (inside)')
    print('==================')
    multi_run_results = multi_run_inside()
    print('Final position mean    :', mean(multi_run_results))
    print('Final position st. dev.:', stdev(multi_run_results))

    print('========================')
    print('Multi run (non-daemonic)')
    print('========================')
    multi_run_nondaemonic_results = multi_run_nondaemonic()
    print('Final position mean    :', mean(multi_run_nondaemonic_results))
    print('Final position st. dev.:', stdev(multi_run_nondaemonic_results))
