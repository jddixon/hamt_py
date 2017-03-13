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

    def make_a_unique_leaf(self, by_keys):
        """
        Make a leaf node with quesi-random key and value.

        The Leaf returned is guaranteed to have a key not already in
        by_keys.
        """

        key = bytes(self.rng.some_bytes(8))
        value = bytes(self.rng.some_bytes(16))
        while key in by_keys:
            key = bytes(self.rng.some_bytes(8))

        return Leaf(key, value)

    def make_a_leaf_cluster(self, texp):
        """
        Make 1 << Leafs with distinct keys and values.
        """
        if texp > 8:
            raise RuntimeError(
                "THIS WON'T WORK: texp is %d but may not exceed 8" % texp)

        key = self.rng.some_bytes(8)
        value = self.rng.some_bytes(16)

        leaves = []
        count = 1 << texp
        mask = count - 1       # we want to mask off that many bits
        shift = 8 - texp         # number of bits to shift the mask
        if texp < 8:
            mask <<= shift

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
        return leaves

    # ---------------------------------------------------------------

    def do_test_full_root(self, texp):
        """
        Test behavior of tree with (nearly) full root with 1 << texp entries.

        We make enough entries to fill the root, then add them one by one.
        If an entry has the same slot number as a previously inserted entry,
        we discard it.
        """

        wexp = texp     # we aren't yet interested in wexp != texp
        slot_count = 1 << texp
        root = Root(wexp, texp)
        self.assertEqual(root.leaf_count, 0)
        self.assertEqual(root.table_count, 1)     # root table is counted

        leaves = self.make_a_leaf_cluster(texp)     # <= 1 << texp unique Leafs
        inserted = 0
        slot_nbrs = []  # list of slot numbers of occupied slots
        by_keys = {}    # Leafs indexed by key
        for leaf in leaves:
            slot_nbr = uhash(leaf.key) & root.mask
            if not slot_nbr in slot_nbrs:
                root.insert_leaf(leaf)
                inserted += 1
                slot_nbrs.append(slot_nbr)
                self.assertEqual(root.leaf_count, inserted)
                self.assertEqual(root.table_count, 1)
                value = root.find_leaf(leaf.key)
                self.assertEqual(value, leaf.value)

                by_keys[leaf.key] = leaf

        # we have successfully inserted that many leaf nodes into the
        # root table.
        self.assertEqual(root.leaf_count, inserted)
        self.assertEqual(len(by_keys), inserted)

        # DEBUG
        print("There are %d/%d entries in the root table." % (
            len(slot_nbrs), slot_count))
        # END

        leaf = self.make_a_unique_leaf(by_keys)
        # this will either be inserted into the root table or into a
        # new table in a root table slot
        root.insert_leaf(leaf)
        inserted += 1
        entry = root.find_leaf(leaf.key)
        self.assertIsNotNone(entry)

    def test_full_root(self):
        """
        Test behavior with full roots of various sizes.

        """
        for texp in [3, 4, 5, 6]:
            self.do_test_full_root(texp)


if __name__ == '__main__':
    unittest.main()
