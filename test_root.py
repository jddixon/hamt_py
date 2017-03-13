#!/usr/bin/env python3
# hamt_py/test_root.py

""" Test properties of the HAMT Root. """

#import hashlib
#import os
import time
import unittest
from binascii import b2a_hex

from rnglib import SimpleRNG
from hamt import Root, Table, Leaf, HamtError, uhash


class TestRoot(unittest.TestCase):
    """ Test properties of the HAMT Root. """

    def setUp(self):
        self.rng = SimpleRNG(time.time())

    def tearDown(self):
        pass

    MAX_T = 8

    def make_a_leaf_cluster(self, texp):
        """
        Make 1 << texp leafs with distinct keys and values.
        """
        if texp > TestRoot.MAX_T:
            raise RuntimeError(
                "THIS WON'T WORK: texp is %d but may not exceed MAX_T=%d" % (
                    texp, TestRoot.MAX_T))

        key = self.rng.some_bytes(8)
        value = self.rng.some_bytes(16)

        leaves = []
        count = 1 << texp
        mask = count - 1       # we want to mask off that many bits
        shift = 8 - texp       # number of bits to shift the mask
        if texp < 8:
            mask <<= shift

        # DEBUG
        # print("make_a_leaf_cluster: texp %d, shift %d, mask 0x%x" % (
        #    texp, shift, mask))
        # END

        key = self.rng.some_bytes(8)
        value = self.rng.some_bytes(16)

        for ndx in range(count):
            slot_nbr = ndx << shift

            mykey = bytearray(8)
            mykey[:] = key              # local copy of key
            myval = bytearray(16)
            myval[:] = value            # local copy of value
            mykey[0] &= ~mask
            mykey[0] |= slot_nbr
            mykey = bytes(mykey)

            myval[0] &= ~mask
            myval[0] |= slot_nbr
            myval = bytes(myval)

            leaf = Leaf(mykey, myval)
            leaves.append(leaf)
            # DEBUG
            # print("%3d key %s value %s" % (
            #    ndx, b2a_hex(mykey), b2a_hex(myval)))
            # END
        return leaves

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

        texp = wexp     # we aren't interested in texp != wexp
        root = Root(wexp, texp)
        self.assertEqual(root.leaf_count, 0)
        self.assertEqual(root.table_count, 1)     # root table is counted

        leaves = self.make_a_leaf_cluster(texp)     # 1 << texp unique Leafs
        inserted = 0
        ndxes = []
        for leaf in leaves:
            ndx = uhash(leaf.key) & root.mask
            if not ndx in ndxes:
                root.insert_leaf(leaf)
                inserted += 1
                ndxes.append(ndx)
                self.assertEqual(root.leaf_count, inserted)
                self.assertEqual(root.table_count, 1)
                value = root.find_leaf(leaf.key)
                self.assertEqual(value, leaf.value)

    def test_flat_root(self):
        """
        Test constructor functionality with a range of parameters.
        """
        for wexp in [3, 4, 5, 6]:
            self.do_test_flat_root(wexp)


if __name__ == '__main__':
    unittest.main()
