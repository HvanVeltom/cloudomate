from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cloudomate',

    version='0.0.1',

    description='Automate buying VPS instances with Bitcoin',
    long_description=long_description,

    url='https://github.com/Jaapp-/Cloudomate',

    author='PlebNet',
    author_email='plebnet@heijligers.me',

    license='LGPLv3',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: System :: Installation/Setup'
        'Topic :: Software Development :: Libraries :: Python Modules',

        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='vps bitcoin',

    packages=find_packages(exclude=['docs', 'tests']),


    install_requires=['scrapy', ],

    extras_require={
        'dev': [],
        'test': [],
    },

    package_data={
        'cloudomate': [],
    },

    entry_points={
        'console_scripts': [
            'cloudomate=cloudomate:main',
        ],
    },
)