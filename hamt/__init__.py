# hamt/__init__.py

""" NodeID library for python XLattice packages. """

__version__ = '0.0.2'
__version_date__ = '2017-03-02'

__all__ = ['__version__', '__version_date__', 'HamtError', ]


class HamtError(RuntimeError):
    """ General purpose exception for the package. """
