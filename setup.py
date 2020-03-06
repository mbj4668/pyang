from setuptools import setup
from setuptools import Distribution
from os.path import join
import pyang
import glob
import os
import re
import sys
import tempfile

modules_iana = glob.glob(os.path.join('modules', 'iana', '*.yang'))
modules_ietf = glob.glob(os.path.join('modules', 'ietf', '*.yang'))
xslt = glob.glob(os.path.join('xslt', '*.xsl'))
schema = glob.glob(os.path.join('schema', '*.rng'))
images = glob.glob(os.path.join('tools', 'images', '*'))
man1 = glob.glob(os.path.join('man', 'man1', '*.1'))

class PyangDist(Distribution):

      """The purpose of this subclass of Distribution is to extend the
      install procedure with preprocessing of shell scripts and man
      pages so that they reflect the actual installation prefix, which
      may be changed through the --prefix option.
      """

      def preprocess_files(self, prefix):
            """Change the installation prefix where necessary.
            """
            if prefix is None: return
            files = ("bin/yang2dsdl", "man/man1/yang2dsdl.1",
                     "pyang/plugins/jsonxsl.py")
            regex = re.compile("^(.*)/usr/local(.*)$")
            for f in files:
                  inf = open(f)
                  cnt = inf.readlines()
                  inf.close()
                  ouf = open(f,"w")
                  for line in cnt:
                        mo = regex.search(line)
                        if mo is None:
                              ouf.write(line)
                        else:
                              ouf.write(mo.group(1) + prefix + mo.group(2) +
                                        "\n")
                  ouf.close()

      def run_commands(self):
            opts = self.command_options
            if "install" in opts:
                  self.preprocess_files(opts["install"].get("prefix",
                                                            ("", None))[1])
            Distribution.run_commands(self)

# If the installation is on windows, place pyang.bat file in Scripts directory
script_files = []
if os.name == "nt":
    pyang_bat_file = "{}/{}.bat".format(tempfile.gettempdir(), "pyang")
    with open(pyang_bat_file, 'w') as script:
        script.write('@echo off\npython %~dp0pyang %*\n')
    script_files = ['bin/pyang', 'bin/yang2html',
                    'bin/yang2dsdl', 'bin/json2xml', pyang_bat_file]
else:
    script_files = ['bin/pyang', 'bin/yang2html',
                    'bin/yang2dsdl', 'bin/json2xml']

setup(name='pyang',
      version=pyang.__version__,
      author='Martin Bjorklund',
      author_email='mbj@tail-f.com',
      description="A YANG (RFC 6020/7950) validator and converter",
      long_description="An extensible  YANG (RFC 6020/7950) validator." + \
      " Provides a framework for plugins that can convert YANG modules" + \
      "to other formats.",
      url='https://github.com/mbj4668/pyang',
      install_requires = ["lxml"],
      license='BSD',
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            ],
      keywords='YANG validator',
      distclass=PyangDist,
      scripts=script_files,
      packages=['pyang', 'pyang.plugins', 'pyang.translators', 'pyang.transforms'],
      data_files=[
            ('share/man/man1', man1),
            ('share/yang/modules/iana', modules_iana),
            ('share/yang/modules/ietf', modules_ietf),
            ('share/yang/xslt', xslt),
            ('share/yang/images', images),
            ('share/yang/schema', schema),
            ('etc/bash_completion.d', ['etc/bash_completion.d/pyang']),
            ]
      )

# Remove Bat file
if os.name == "nt":
    os.remove(pyang_bat_file)
