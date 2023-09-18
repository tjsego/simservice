import os
import sys
import unittest

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import RandomWalkerUser


class RandomWalkerTestCase(unittest.TestCase):

    def test_single_run(self):
        RandomWalkerUser.single_run()

    def test_multi_run(self):
        RandomWalkerUser.multi_run()

    def test_multi_run_inside(self):
        RandomWalkerUser.multi_run_inside()

    def test_multi_run_nondaemonic(self):
        RandomWalkerUser.multi_run_nondaemonic()
