#!/usr/bin/env python3
# hamt_py/test_table.py

""" Test properties of the HAMT Table. """

# import hashlib
# import os
import time
import unittest

from rnglib import SimpleRNG
from hamt import HamtNotFound, Root, Leaf, uhash


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

    def make_many_leaves(self, count):
        """
        Make count Leafs with distinct keys.
        """
        if count < 1:
            count = 16
        else:
            count &= 0xffffffff        # arbitrary limit
        leaves = []
        keys = set()

        for _ in range(count):
            key = bytes(self.rng.some_bytes(8))
            while key in keys:
                key = bytes(self.rng.some_bytes(8))
            # we have a unique key; add it to the set
            keys.add(key)

            # generate a quasi-random value
            val = bytes(self.rng.some_bytes(16))
            leaf = Leaf(key, val)
            leaves.append(leaf)
        return leaves

    def make_matching_leaves(self, texp):
        """
        Make Leafs whose hcodes the same low-order texp x 4 bits.

        This assumes texp == wexp.
        """
        keylen = ((4 * texp) + 7) // 8        # that many bytes
        # DEBUG
        # print("keylen is %d bytes" % keylen)
        # END

        suffix_len = 4 * texp   # that many bits
        mask = (1 << suffix_len) - 1

        key0 = bytes(self.rng.some_bytes(keylen))
        hcode0 = uhash(key0)
        low_bits0 = hcode0 & mask
        leaves = []

        # DEBUG
        # print("low order bits: 0x%x" % low_bits0)
        # END
        for _ in range(4):          # we want three or more matching keys
            key = bytes(self.rng.some_bytes(8))
            low_bits = mask & uhash(key)
            while low_bits != low_bits0:
                key = bytes(self.rng.some_bytes(8))
                low_bits = mask & uhash(key)
            # DEBUG
            # print("low order bits: 0x%x" % low_bits0)
            # END
            val = bytes(self.rng.some_bytes(16))
            leaf = Leaf(key, val)
            leaves.append(leaf)
        # DEBUG
        # print("generated %d Leafs" % len(leaves))
        # END
        return leaves

    # ---------------------------------------------------------------

    def do_test_fullish_root(self, texp):
        """
        Test behavior of tree with (nearly) full root with 1 << texp entries.

        We make enough entries to fill the root, then add them one by one.
        If an entry has the same slot number as a previously inserted entry,
        we discard it.
        """

        wexp = texp     # we aren't yet interested in wexp != texp
        root = Root(wexp, texp)
        self.assertEqual(root.leaf_count, 0)
        self.assertEqual(root.table_count, 1)     # root table is counted

        leaves = self.make_a_leaf_cluster(texp)     # <= 1 << texp unique Leafs
        inserted = 0
        slot_nbrs = []  # list of slot numbers of occupied slots
        by_keys = {}    # Leafs indexed by key
        for leaf in leaves:
            slot_nbr = uhash(leaf.key) & root.mask
            if slot_nbr not in slot_nbrs:
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

        leaf = self.make_a_unique_leaf(by_keys)
        # this will either be inserted into the root table or into a
        # new table in a root table slot
        root.insert_leaf(leaf)
        inserted += 1
        entry = root.find_leaf(leaf.key)
        self.assertIsNotNone(entry)

    def test_fullish_root(self):
        """
        Test behavior with fullish roots of various sizes.

        We partially fill the root and then add one more leaf, which
        more often than not splits a slot in the Root table.  Sometimes
        it splits a slot in the child Table.

        """
        for _ in range(64):
            for texp in [3, 4, 5, 6]:
                self.do_test_fullish_root(texp)

    # ---------------------------------------------------------------

    def do_test_with_many_keys(self, texp):
        """
        Test behavior of tree where we insert many more Leafs than are
        necessary to fill the root.
        """

        wexp = texp     # we aren't yet interested in wexp != texp
        slot_count = 1 << texp
        root = Root(wexp, texp)
        self.assertEqual(root.leaf_count, 0)
        self.assertEqual(root.table_count, 1)     # root table is counted

        # add all the leafs -------------------------------
        leaves = self.make_many_leaves(slot_count * 2)
        inserted = 0
        for leaf in leaves:
            root.insert_leaf(leaf)
            inserted += 1
            self.assertEqual(root.leaf_count, inserted)

        # verify they are all there -----------------------
        for leaf in leaves:
            value = root.find_leaf(leaf.key)
            self.assertEqual(value, leaf.value)

        # we have successfully inserted that many leaf nodes into the tree
        self.assertEqual(root.leaf_count, inserted)

        # now delete each of the keys ---------------------
        for leaf in leaves:
            # the leaf is present
            value = root.find_leaf(leaf.key)
            self.assertEqual(value, leaf.value)

            # delete the leaf
            root.delete_leaf(leaf.key)

            # verify that now it's gone
            try:
                value = root.find_leaf(leaf.key)
            except HamtNotFound:
                # success, it's gone
                pass

        # verify the count is zero
        self.assertEqual(root.leaf_count, 0)

    def test_with_many_keys(self):
        """
        Test behavior with various values of texp and many more Leafs
        than needed to fill the Root table.
        """
        for texp in [3, 4, 5, 6]:
            self.do_test_with_many_keys(texp)

    # ---------------------------------------------------------------

    def do_test_with_matching_keys(self, texp):
        """
        Run matching-keys test with a specific value of t.

        We create a set of Leafs whose hcodes have the same low-order
        bits (so that they collide on insertion, causing splitting).
        """
        wexp = texp
        root = Root(wexp, texp)
        self.assertEqual(root.leaf_count, 0)
        self.assertEqual(root.table_count, 1)     # root table is counted

        leaves = self.make_matching_leaves(texp)
        inserted = 0
        for leaf in leaves:
            root.insert_leaf(leaf)
            inserted += 1
            self.assertEqual(root.leaf_count, inserted)

        for leaf in leaves:
            value = root.find_leaf(leaf.key)
            self.assertEqual(value, leaf.value)

        # we have successfully inserted that many leaf nodes into the tree
        self.assertEqual(root.leaf_count, inserted)

    def test_with_matching_keys(self):
        """
        Run matching-keys test with a range of t values.

        Computing matching keys is very slow, so we do not test t = 6.
        """
        for texp in [3, 4, 5]:
            self.do_test_with_matching_keys(texp)


if __name__ == '__main__':
    unittest.main()
