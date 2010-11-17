from distutils.core import setup
import pyang
import glob
import os

modules = glob.glob(os.path.join('modules', '*.yang'))
xslt = glob.glob(os.path.join('xslt', '*.xsl'))

setup(name='pyang',
      version=pyang.__version__,
      author='Martin Bjorklund',
      author_email='mbj@tail-f.com',
      description="A YANG (RFC 6020) validator and converter",
      url='http://code.google.com/p/pyang',
      scripts=['bin/pyang', 'bin/yang2html', 'bin/yang2dsdl'],
      packages=['pyang', 'pyang.plugins', 'pyang.translators'],
      data_files=[('.', ['LICENSE']),
                  ('share/man/man1', ['man/man1/pyang.1',
                                      'man/man1/yang2dsdl.1']),
                  ('share/yang/modules', modules),
                  ('share/yang/xslt', xslt),
                  ('share/yang/schema', ['schema/yin.rng',
                                         'schema/relaxng-lib.rng'])]
      )
      
