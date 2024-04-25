from os import path
from setuptools import find_packages, setup

if path.exists('README.md'):
    with open('README.md') as readme:
        long_description = readme.read()


setup(
    name="amber",
    version='0.0.dev0',
    description="AMBER for running simulation grids, and associated analysis.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/enigma-igm/amber",
    author='Trac and Chen for original, CCD for modifications.',
    packages=find_packages(exclude=["tests"]),
)

