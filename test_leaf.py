#!/usr/bin/env python3
# hamt_py/test_basics.py

""" Test properties of the HAMT leaf. """

#import hashlib
#import os
import time
import unittest

from rnglib import SimpleRNG
from hamt import Leaf, HamtError


class TestLeaf(unittest.TestCase):
    """ Test properties of the HAMT leaf. """

    def setUp(self):
        self.rng = SimpleRNG(time.time())

    def tearDown(self):
        pass

    def test_ctor(self):
        """
        Test constructor functionality.
        """

        # tests that should raise an exception

        with self.assertRaises(HamtError):
            leaf = Leaf(None, 'some random value')
        with self.assertRaises(HamtError):
            leaf = Leaf(b'some key', None)

        # tests that should succeed
        key = self.rng.some_bytes(8)
        value = self.rng.some_bytes(16)
        leaf = Leaf(key, value)
        self.assertEqual(leaf.key, key)
        self.assertEqual(leaf.value, value)

        self.assertTrue(isinstance(leaf, Leaf))

if __name__ == '__main__':
    unittest.main()
