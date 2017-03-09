#!/usr/bin/env python3
# hamt_py/test_root.py

""" Test properties of the HAMT Root. """

#import hashlib
#import os
import time
import unittest

from rnglib import SimpleRNG
from hamt import Root, Table, Leaf, HamtError


class TestRoot(unittest.TestCase):
    """ Test properties of the HAMT Root. """

    def setUp(self):
        self.rng = SimpleRNG(time.time())

    def tearDown(self):
        pass

    def make_a_leaf(self):
        """ Create a Leaf with quasi-random key and value. """
        key = bytes(self.rng.some_bytes(8))
        value = bytes(self.rng.some_bytes(16))
        return Leaf(key, value)

    # ---------------------------------------------------------------

    def do_test_root_ctor(self, wexp):
        """ Test Root constructor with specific parameters. """

        texp = wexp + self.rng.next_int16(4)
        root = Root(wexp, texp)
        self.assertIsNotNone(root)
        self.assertEqual(root.wexp, wexp)
        self.assertEqual(root.texp, texp)
        self.assertEqual(root.max_table_depth, (64 - texp) // wexp)

        self.assertIsNotNone(root.slots)
        self.assertEqual(len(root.slots), 1 << texp)     # 0)

        self.assertEqual(root.slot_count, 1 << texp)
        self.assertEqual(root.mask, root.slot_count - 1)

    def test_ctor(self):
        """
        Test constructor functionality with a range of parameters.
        """
        for wexp in [3, 4, 5, 6]:
            self.do_test_root_ctor(wexp)

    # ---------------------------------------------------------------

    def do_test_flat_root(self, wexp):
        """ Test insertions only into the root table for the value of wexp. """

        texp = wexp + self.rng.next_int16(4)
        root = Root(wexp, texp)
        self.assertEqual(root.leaf_count(), 0)
        self.assertEqual(root.table_count(), 1)     # root table is counted

        # we make a random Leaf
        leaf = self.make_a_leaf()
        # and add it to the Root
        root.insert_leaf(leaf)
        self.assertEqual(root.leaf_count(), 1)      # we have added one leaf
        self.assertEqual(root.table_count(), 1)     # just the root table

    def test_flat_root(self):
        """
        Test constructor functionality with a range of parameters.
        """
        for wexp in [3, 4, 5, 6]:
            self.do_test_flat_root(wexp)


if __name__ == '__main__':
    unittest.main()
