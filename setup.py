from setuptools import setup
import io

setup(
    name='configtamer',
    author='Rodrigo Bernardo Pimentel',
    author_email='rbp@isnomore.net',
    version='0.1',
    packages=['configtamer'],
    license='Apache License, Version 2.0',
    description="configuration file parsing under control",
    long_description="A clean, flexible configuration file format (and parser).",
    url='https://github.com/rbp/configtamer',

    install_requires=['parsimonious>=0.5'],
    
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        ),
    )
