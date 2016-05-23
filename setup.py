"""Setup program for pyfind CLI tool
"""
from setuptools import setup

setup(
    name='Pyfind',
    version='1.0',
    license='MIT License',
    author='Doug Mahugh',
    py_modules=['pyfind'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        pyfind=pyfind:cli
    '''
)