# hamt/__init__.pyMT

""" NodeID library for python XLattice packages. """

import sys

from xlutil import popcount64

__version__ = '0.1.2'
__version_date__ = '2017-03-10'

__all__ = ['__version__', '__version_date__',
           'MAX_W',
           'uhash',
           'HamtError', 'HamtNotFound',
           'Leaf', 'Table', 'Root']

# CONSTANTS

MAX_W = 6

# FUNCTIONS


def bytes_equal(aaa, bbb):
    if not (isinstance(aaa, bytes) and isinstance(bbb, bytes)):
        return False
    if len(aaa) == 0 or len(aaa) != len(bbb):
        return False
    for ndx, aval in enumerate(aaa):
        if aval != bbb[ndx]:
            return False
    return True


def uhash(val):
    """ Return the hash of a string of bytes as an unsigned int64. """
    return hash(val) % ((sys.maxsize + 1) * 2)

# CLASSES


class HamtError(RuntimeError):
    """ General purpose exception for the package. """


class HamtNotFound(HamtError):
    """ Raised where there is no match for a key. """


class Leaf(object):
    """The Leaf in a HAMT data structure. """

    def __init__(self, key, value):

        if key is None:
            raise HamtError('key cannot be None')
        if value is None:
            raise HamtError("leaf value cannot be none")
        self._key = key
        self._value = value

    @property
    def key(self):
        """ Return the key part of a HAMT Leaf."""
        return self._key

    @property
    def value(self):
        """ Return the value pointed at by a HAMT Leaf. """
        return self._value

    @property
    def is_leaf(self):
        """ Return whether this Leaf is indeed a Leaf. """
        return True


class Table(object):
    """
    Table with a dynamic number of entries.

    The number of slots may grow to to a maximum of (1 << wexp).
    Each slot is either empty or points to either a Leaf or another Table.

    Unlike the Go version, a hamt_py Table can only be created if its
    first leaf is specified.  That is, __init__() below is equivalent to
    Go hamt_go's NewTableWithLeaf.
    """

    @staticmethod
    def check_table_param(depth, root):  # -> (int, int)
        """ Raise if table parameter is out of range. """
        if root is None:
            raise HamtError("root must have a value")
        wexp = root.wexp
        texp = root.texp
        if wexp > MAX_W:
            raise HamtError("Max table size exceeded.")
        if texp + (depth - 1) * wexp > 64:
            raise HamtError("Max table depth exceeded.")
        return wexp, texp           # Seen as unsigned ints

    def __init__(self, depth, root, first_leaf):
        wexp, texp = Table.check_table_param(depth, root)
        self._wexp = wexp
        self._texp = texp
        self._root = root
        wflag = 1 << wexp            # seen as uint64
        self._mask = wflag - 1       # ditto

        shift_count = texp + (depth - 1) * wexp
        hcode = uhash(first_leaf.key) >> shift_count
        ndx = hcode & self._mask
        flag = 1 << ndx             # seen as uint64
        self._slots = [first_leaf]
        self._bitmap = flag         # seen as uint64
        # DEBUG
        print("new Table:      depth  = %d" % depth)
        print("                texp   = %d" % texp)
        print("                wexp   = %d" % wexp)
        print("                wflag  = %d" % wflag)
        print("                mask   = %d" % self._mask)
        print("    first leaf: ndx    = %d (0x%x)" % (ndx, ndx))
        print("                flag   = 0x%x" % flag)
        print("    Table:      bitmap = 0x%x" % self._bitmap)
        # END

    @property
    def root(self):
        """ Return the Root of the table. """
        return self._root

    @property
    def wexp(self):
        """
        Return the w factor, where 2^w is the number of slots in the Table.
        """
        return self._wexp

    @property
    def texp(self):
        """
        Return the t factor, where 2^t is the number of slots in the Root.
        """
        return self._texp

    @property
    def mask(self):
        """ Return a bit vectory with the bit set if the slot is free. """
        return self._mask

    @property
    def slots(self):
        return self._slots

    @property
    def bitmap(self):
        return self._bitmap

    @property
    def max_slots(self):
        """
        Return one more than the maximum number of slots that may be
        occupied.
        """
        return 1 << self._wexp

    @property
    def leaf_count(self):
        """ Return a count of the leaf nodes in this Table, recursing. """
        count = 0
        # for node in self._slots:
        for ndx, node in enumerate(self._slots):
            if node:
                if node.is_leaf:
                    count += 1
                    # DEBUG
                    print("slot %3d is Leaf" % ndx)
                    # END
                else:
                    # DEBUG
                    print("slot %3d is Table" % ndx)
                    # END
                    # regarding the node as a Table:
                    count += node.table_count
        # DEBUG
        print("Table.leaf_count returning %d" % count)
        # END
        return count

    @property
    def table_count(self):
        """
        Return a count of Table nodes below this Table (or Root),
        including this Table.
        """
        count = 1       # this Table
        for node in self._slots:
            if node and not node.is_leaf:
                count += node.table_count
        return count

    def remove_from_slots(self, offset):
        """ Remove an entry from this Table. """

        cursize = len(self._slots)
        if cursize == 0:
            raise HamtError("attempt to delete from empty Table")
        if offset >= cursize:
            msg = 'Internal error: delete offset %d but table size %d' % (
                offset, cursize)
            raise HamtError(msg)
        elif cursize == 1:
            # LEAVES EMPTY TABLE, WHICH WILL HARM PERFORMANCE
            self._slots = []
        elif offset == 0:
            self._slots = self._slots[1:]
        elif offset == cursize - 1:
            self._slots = self._slots[:-1]
        else:
            self._slots = self._slots[:offset] + self._slots[offset + 1:]

    def delete_leaf(self, hcode, depth, key):       # KEY, DEPTH not used?
        """
        Remove a Leaf from the Table.

        Enter with hcode the hashcode for the key shifted appropriately
        for the current depth, so that the first w bits of the shifted
        hashcod can be used as the index of the leaf in the table.

        The caller guarantees that depth <= root.max_table_depth.
        """

        if len(self._slots) == 0:
            raise HamtNotFound

        ndx = hcode & self._mask
        flag = 1 << ndx             # a uint64
        mask = flag - 1
        if self._bitmap & flag == 0:
            raise HamtNotFound

        # the node is present: get its position in the slice
        slot_nbr = 0
        if mask:
            slot_nbr = popcount64(self._bitmap & mask)
        node = self._slots[slot_nbr]
        if node.is_leaf:
            # key = node.key        # REDUNDANT?
            if node.key == key:
                self.remove_from_slots(slot_nbr)
                self._bitmap &= ~flag           # TEST
            else:
                raise HamtNotFound
        else:
            # node is a table, so recurse
            depth += 1
            if depth > self.root.max_table_depth:
                raise HamtNotFound
            hcode >>= self._wexp
            node.delete_leaf(hcode, depth, key)

    def find_leaf(self, hcode, depth, key):
        """
        Find a Leaf using the hashcode hcode and matching depth and key.

        The hashcode has been shifted appropriately for the current
        depth (zero-based).  Return None if no matching entry is found
        or the value associated with the key.

        The caller guarantees that depth <= Root.max_table.depth.
        """

        value = None
        ndx = hcode & self._mask    # uint
        flag = 1 << ndx             # uint64

        if self._bitmap & flag:
            # the node is present
            slot_nbr = 0
            mask = flag - 1         # also uint64
            if mask:
                slot_nbr = popcount64(self._bitmap & mask)
            node = self._slots[slot_nbr]
            if node.is_leaf:
                if key == node.key:
                    value = node.value
            else:
                # node is a Table, so recurse
                depth += 1
                if depth <= self.root.max_table_depth:
                    hcode += self._wexp
                    value = node.findLeaf(hcode, depth, key)
        return value

    def insert_leaf(self, hcode, depth, leaf):
        """
        Enter with hcode having been shifted so that the first wexp bits
        are ndx.

        The caller guarantees that depth <= self.root.max_table_depth.
        """

        slot_nbr = 0
        ndx = hcode & self._mask
        flag = 1 << ndx             # uint64
        mask = flag - 1
        if mask:
            slot_nbr = popcount64(self._bitmap & mask)
        slice_size = len(self._slots)
        # DEBUG
        print("Table.insert_leaf: depth      = %d" % depth)
        print("                   slot_nbr   = %d" % slot_nbr)
        print("                   ndx        = 0x%x" % ndx)
        print("                   flag       = 0x%x" % flag)
        print("                   mask       = 0x%x" % mask)
        print("                   slice_size = %d" % slice_size)
        # END

        if slice_size == 0:
            slice_size = 1 << self._wexp
            self._slots = [None] * self._wexp
            self._slots[ndx] = leaf
            self._bitmap |= flag
        else:
            # is there already something in this slot?
            if self._bitmap & flag:
                entry = self._slots[slot_nbr]
                if entry is None:
                    print("INTERNAL ERROR: flag=%d, slot=%d is empty" % (
                        flag, slot_nbr))

                if entry.is_leaf:
                    if entry.key == leaf.key:
                        # keys match so replace value
                        entry.value = leaf.value        # MUST BE DEEPCOPY ?
                    else:
                        depth += 1
                        if depth > self._root.max_table_depth:
                            raise HamtError(
                                "max table depth %d exceeded" %
                                self._root.max_table_depth)
                        deeper = Table(depth, self._root, leaf)
                        # the new table replaces the existing leaf
                        self._slots[slot_nbr] = deeper

                else:   # it's a Table
                    depth += 1
                    if depth > self._root.max_table_depth:
                        raise HamtError('max table depth exceeded')
                    # it's a Table, so let's recurse
                    hcode >>= self._wexp
                    entry.insert_leaf(hcode, depth, leaf)

            # nothing in the slot
            elif slot_nbr == 0:
                self._slots = [leaf] + self._slots
                self._bitmap |= flag
            elif slot_nbr == slice_size:
                self._slots += leaf
                self._bitmap |= flag
            else:
                self._slots = self._slots[:slot_nbr] + \
                    [leaf] + self._slots[slot_nbr:]
                self._bitmap |= flag

    def is_leaf(self):
        """ Return whether this is a Leaf (it isn't). """
        return False


class Root(object):
    """
    Root table of a HAMT Trie.

    The Root has a fixed number of slots, each of which may be empty
    or may point to a Table or a Leaf.  There are (1 << texp) slots
    in the Root table.
    """

    def __init__(self, wexp, texp):
        if wexp < 2:
            raise HamtError("w cannot be less than 2, is %d" % wexp)
        if texp < 2:
            raise HamtError("w cannot be less than 2, is %d" % texp)
        if wexp > MAX_W:
            raise HamtError("max table size (%d) exceeded" % MAX_W)
        if texp > 64:
            raise HamtError("max root table size (64) exceeded")
        flag = 1 << texp    # number of slots available

        self._wexp = wexp
        self._texp = texp
        self._max_table_depth = (64 - texp) // wexp
        self._slot_count = flag
        self._mask = flag - 1
        self._slots = [None] * flag
        # DEBUG
        print("Root: wexp            %d" % wexp)
        print("      texp            %d" % texp)
        print("      max table depth %d" % self.max_table_depth)
        print("      slot count      %d" % flag)
        print("      mask            0x%x" % self._mask)
        # END

    @property
    def wexp(self):
        """
        Return the w factor, where 2^w is the number of slots in the Table.
        """
        return self._wexp

    @property
    def texp(self):
        """
        Return the t factor, where 2^t is the number of slots in the Root.
        """
        return self._texp

    @property
    def max_table_depth(self):
        """
        Return the nmaximum number of slots in the Root or any descendents.
        """
        return self._max_table_depth

    @property
    def slot_count(self):
        """ Return the number of slots in the root table.  """
        return self._slot_count

    @property
    def mask(self):
        """ A mask of bits: 1 if the slot is free, 0 if not. """
        return self._mask

    @property
    def slots(self):
        """ Return the slots table for the Root. """
        return self._slots

    @property
    def leaf_count(self):
        """ Return a count of leaf nodes under the Root. """
        count = 0
        # for node in self._slots:
        for ndx, node in enumerate(self._slots):
            if node:
                if node.is_leaf:
                    count += 1
                    # DEBUG
                    print("root slot %3d is Leaf" % ndx)
                    # END
                else:
                    # DEBUG
                    print("root slot %3d is Table" % ndx)
                    # END
                    # recurse
                    count += node.leaf_count
        # DEBUG
            # else:
            #    print("root slot %03d is EMPTY" % ndx)
        print("             returning Root leaf count %d" % count)
        # END
        return count

    @property
    def table_count(self):
        """
        Return a count of Tables under the Root, including the Root itself.
        """
        count = 1       # the Root
        for node in self._slots:
            if node and not node.is_leaf:
                count += node.table_count
        return count

    def delete_leaf(self, key):
        """ Find a delete a Leaf node in or below this Root, given its key. """

        hcode = uhash(key)
        ndx = hcode & self._mask
        node = self._slots[ndx]
        if node is None:
            raise HamtNotFound
        if node.is_leaf:
            if node.key == key:
                self._slots[ndx] = None
            else:
                raise HamtNotFound
        else:
            # entry is a Table, so recurse
            if self._max_table_depth < 1:
                raise HamtNotFound
            else:
                hcode >>= self._texp
            node.delete_leaf(hcode, 1, key)

    def find_leaf(self, key):
        """
        Given a properly shifted hashcode and the key for an entry,
        return the value associated with the key or None if there
        is no such value.
        """

        value = None
        hcode = uhash(key)
        ndx = hcode & self._mask
        node = self._slots[ndx]

        if node:
            if node.is_leaf:
                if node.key == key:
                    value = node.value
            else:
                if self._max_table_depth > 0:
                    # it's a Table, so recurse
                    hcode >>= self._texp
                    value = node.find_leaf(hcode, 1, key)
        return value

    def insert_leaf(self, leaf):
        """ Insert a Leaf into or below the Root. """

        hcode = uhash(leaf.key)
        ndx = hcode & self._mask        # slot number
        # DEBUG
        print("insert_leaf: hcode 0x%x" % hcode)
        print("             mask  0x%x" % self._mask)
        print("             ndx   0x%x (%d)" % (ndx, ndx))
        # END
        node = self._slots[ndx]

        if node is None:
            # the slot is empty
            self._slots[ndx] = leaf
        else:
            # there is something already in the slot
            if node.is_leaf:
                # it's a leaf; replace value iff the keys match
                cur_key = node.key
                new_key = leaf.key
                if cur_key == new_key:
                    # keys match
                    # DEBUG
                    print("Root.insert_leaf: keys match, so overwriting val")
                    # END
                    node.value = leaf.value
                else:
                    # keys differ, so we replace node with a Table
                    if self._max_table_depth < 1:
                        raise HamtError(
                            "max table depth (%d) exceeded" %
                            self._max_table_depth)
                    new_hcode = hcode >> self._texp    # hcode for new entry

                    # DEBUG
                    print("Root.insert_leaf: keys differ, replacing with Table")
                    # END

                    new_table = Table(1, self, leaf)
                    new_table.insert_leaf(new_hcode, 1, node)
                    self._slots[ndx] = new_table
            else:
                # DEBUG
                print("Root.insert_leaf: node is Table")
                # END
                # it's a table
                if self._max_table_depth < 1:
                    raise HamtError(
                        "max table depth (%d) exceeded" %
                        self._max_table_depth)
                new_hcode = hcode >> self._texp    # hcode for new entry
                node.insert_leaf(new_hcode, 1, leaf)
