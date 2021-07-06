# setup.py
import sys
from setuptools import setup
from setuptools import find_packages

# The version is updated automatically with bumpversion
# Do not update manually
__version = '2.1.0'

# windows installer:
# python setup.py bdist_wininst

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords

setup_requirements = []

setup(
    name="oxfcryo700",
    description="Python Oxford CryoSystem Tango Device Server",
    version=__version,
    author="Zbigniew Reszela et al.",
    author_email="ctbeamlines@cells.es",
    url="https://github.com/ALBA-Synchrotron/OxfCryo700",
    packages=find_packages(),
    # package_data={'': package_list},
    include_package_data=True,
    license="GPLv3",
    long_description="Python Oxford CryoSystem Tango Device Server for 600 "
                     "and 700 series",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.5',
        'Topic :: Communications',
        'Topic :: Software Development :: Libraries',
    ],
    entry_points={
        'console_scripts': [
            'OxfCryo700 = oxfcryo700.tango:main',

        ]
    },
    install_requires=['pyserial', 'pytango'],
    python_requires='>=3.5',
)
