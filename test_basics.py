#!/usr/bin/env python3
# hamt_py/test_basics.py

""" Currently just exercises test framework. """

#import hashlib
#import os
import time
import unittest

from rnglib import SimpleRNG
from hamt import *


class TestWhatever(unittest.TestCase):
    """ Currently just exercises test framework. """

    def setUp(self):
        self.rng = SimpleRNG(time.time())

    def tearDown(self):
        pass

    def test_whatever(self):
        """
        Tests nothing at all.
        """

        self.assertEqual(1, 1)

if __name__ == '__main__':
    unittest.main()
