#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup

setup(name='py-ucengine',
      version='0.6',
      package_dir={'': 'src'},
      url='http://github.com/athoune/py-ucengine',
      #scripts=[],
      description="Python client for UCEngine",
      license="LGPL",
      author="Mathieu Lecarme",
      packages=['ucengine'],
      keywords= [''],
      zip_safe = True,
      install_requires=["gevent", "requests"]
      )