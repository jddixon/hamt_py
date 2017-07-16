#!/usr/bin/python3
# hamt_py/setup.py

""" Setuptools project configuration for hamt_py. """

import re
from glob import glob
from os.path import basename, dirname, exists, join, splitext
from setuptools import find_packages, setup

# replace with literal
__version__ = re.search(r"__version__\s*=\s*'(.*)'",
                        open('src/hamt/__init__.py').read()).group(1)

# see
# setuptools.readthedocs.io/en/latest/setuptools.html#new-and-changed-setup-keywords

long_desc = None
if exists('README.md'):
    with open('README.md', 'r') as file:
        long_desc = file.read()

setup(name='hamt_py',
      version=__version__,
      author='Jim Dixon',
      author_email='jddixon@gmail.com',

      long_description=long_desc,
      # packages=find_packages('src'),
      packages=['hamt'],                                   # LITERAL
      package_dir={'': 'src'},
      py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
      include_package_data=False,
      zip_safe=False,

      scripts=[],
      description='generator for hamt_py projects',
      url='https://jddixon.github.com/hamt_py',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',                # VARIES
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',             # VARIES
          'Natural Language :: English',
          'Programming Language :: Python 3',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],)
