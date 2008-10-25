from distutils.core import setup
import pyang
import glob

modules = glob.glob('modules/*.yang')

setup(name='pyang',
      version=pyang.__version__,
      author='Martin Bjorklund',
      author_email='mbj@tail-f.com',
      description="A YANG validator and converter",
      url='http://code.google.com/p/pyang',
      scripts=['bin/pyang'],
      packages=['pyang', 'pyang.plugins', 'pyang.translators'],
      data_files=[('share/man/man1', ['man/man1/pyang.1']),
                  ('share/yang/modules', modules)],
      )
