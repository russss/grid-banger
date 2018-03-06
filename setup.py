#!/usr/bin/python

import distutils.core

distutils.core.setup(
    name='osgb',
    version='1.0.0',
    description='osgb - high-precision geographic coordinate conversion for Great Britain, based on Ordnance Survey data',
    license='MIT Licence',
    author='Toby Thurston',
    author_email='toby@cpan.org',
    url='http://thurston.eml.cc',
    packages=['osgb'],
    package_data={'osgb': ['ostn_east_shift_82140', 'ostn_north_shift_-84180', 'gb_coastline.shapes']},
    scripts=['scripts/bngl', 'scripts/plot_maps.py'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    keywords='GIS geographic coordinates conversion',
)
