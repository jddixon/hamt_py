# hamt/__init__.pyMT

""" NodeID library for python XLattice packages. """

import sys

__version__ = '0.0.3'
__version_date__ = '2017-03-03'

__all__ = ['__version__', '__version_date__', 'HamtError', 'MAX_W',
           'Leaf', ]

# CONSTANTS
MAX_W = 6

# FUNCTIONS


def uhash(val):
    """ Return the hash of a string of bytes as an unsigned int64. """
    return hash(val) % ((sys.maxsize + 1) * 2)

# CLASSES


class HamtError(RuntimeError):
    """ General purpose exception for the package. """


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
