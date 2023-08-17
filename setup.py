import os
from setuptools import setup

__version__ = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'simservice', 'VERSION.txt')).readline().strip()

setup(
    name='simservice',
    version=__version__,
    description='A library for building simulation services in Python',
    url='https://github.com/tjsego/simservice',
    author='T.J. Sego',
    author_email='timothy.sego@medicine.ufl.edu',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Science/Research',

        'License :: OSI Approved :: MIT License',

        'Operating System :: OS Independent',

        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    packages=['simservice'],
    package_dir={'simservice': 'simservice'},
    python_requires='>=3.6',
    package_data={'simservice': ['../LICENSE', 'VERSION.txt']}
)
