#!/usr/bin/env python3
# hamt_py/test_table.py

""" Test properties of the HAMT Table. """

#import hashlib
#import os
import time
import unittest
from binascii import b2a_hex

from rnglib import SimpleRNG
from hamt import Root, Table, Leaf, HamtError, uhash


class TestTable(unittest.TestCase):
    """ Test properties of the HAMT Table. """

    def setUp(self):
        self.rng = SimpleRNG(time.time())

    def tearDown(self):
        pass

    def make_a_leaf_cluster(self, nnn):
        """
        Make 2^nnn leafs with distinct keys and values.  If nnn <= texp,
        these will fit into the root table.
        """
        if nnn > 8:
            raise RuntimeError(
                "THIS WON'T WORK: nnn is %d but may not exceed 8" % nnn)

        key = self.rng.some_bytes(8)
        value = self.rng.some_bytes(16)

        leaves = []
        count = 1 << nnn
        mask = count - 1       # we want to mask off that many bits
        shift = 8 - nnn         # number of bits to shift the mask
        if nnn < 8:
            mask <<= shift

        # DEBUG
        # print("make_a_leaf_cluster: nnn %d, shift %d, mask 0x%x" % (
        #    nnn, shift, mask))
        # END

        key = self.rng.some_bytes(8)
        value = self.rng.some_bytes(16)

        for ndx in range(count):
            xxx = ndx << shift

            mykey = bytearray(8)
            mykey[:] = key              # local copy of key
            myval = bytearray(16)
            myval[:] = value            # local copy of value
            mykey[0] &= ~mask
            mykey[0] |= xxx
            mykey = bytes(mykey)

            myval[0] &= ~mask
            myval[0] |= xxx
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
        """ Test Table constructor with specific parameters. """

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
        """ XXX RETHINK, THEN REWRITE. """

        texp = wexp     # we aren't interested in textp != wexp
        root = Root(wexp, texp)
        self.assertEqual(root.leaf_count, 0)
        self.assertEqual(root.table_count, 1)     # root table is counted

        leaves = self.make_a_leaf_cluster(texp)     # 2^text unique Leafs
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
                # XX FIND RETURNS ENTRY
                found = root.find_leaf(leaf.key)
                self.assertEqual(found.key, leaf.key)
                # VERIFY THAT IT'S A LEAF
                self.assertTrue(found.is_leaf)

        # we have successfully inserted that many leaf nodes into the
        # root table.
        self.assertEqual(root.leaf_count, inserted)

        # WORKING HERE ?

    def test_flat_root(self):
        """
        Test constructor functionality with a range of parameters.
        """
        for wexp in [3, 4, 5, 6]:
            self.do_test_flat_root(wexp)


if __name__ == '__main__':
    unittest.main()
