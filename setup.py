#!/usr/bin/env python3
from setuptools import setup

setup(
    name='bitlish-client',
    version=0.1,
    install_requires=['asyncio', 'websockets'],
    author='Dmitry Sorokin',
    url='https://github.com/asfin/bitlish-client',
    description='Official Bitlish.com WebSocket API wrapper with events support',
    classifiers=[
        'Programming Language :: Python :: 3.4'
    ]
)

