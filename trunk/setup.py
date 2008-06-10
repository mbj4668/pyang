from distutils.core import setup
import pyang
setup(name='pyang',
      version=pyang.__version__
      author='Martin Bjorklund',
      description="A YANG validator and converter",
      scripts=['bin/pyang'],
      packages=['pyang', 'pyang.plugins'],
      )
