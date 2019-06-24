import os
from setuptools import find_packages, setup

setup(
    name='app',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Environment :: Console',
        'Development Status :: 2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',

    ],
)
