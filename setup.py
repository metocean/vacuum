#!/usr/bin/env python
import re
import sys
import os

from setuptools import setup, find_packages

version = re.compile(r'VERSION\s*=\s*\((.*?)\)')

def get_package_version():
    "returns package version without importing it"
    base = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(base, "vacuum/__init__.py")) as initf:
        for line in initf:
            m = version.match(line.strip())
            if not m:
                continue
            return ".".join(m.groups()[0].split(", "))

def get_requirements(filename):
    return open(filename).read().splitlines()


install_requires = get_requirements('requirements.txt')
if sys.version_info < (3, 0):
    install_requires.append('futures')

setup(name='vacuum',
      version=get_package_version(),
      description='Handle cleanup and archive operations based on RE patterns or a YAML file with multiple parameters',
      author='Andre Lobato',
      author_email='andre@metocean.co.nz',
      url='https://github.com/metocean/vacuum',
      license='MIT',
      packages=['vacuum'],
      install_requires=install_requires,
      entry_points={
        'console_scripts': [
            'vacuum = vacuum.__main__:main',
        ],
      },  

     )  