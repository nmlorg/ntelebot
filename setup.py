import setuptools


setuptools.setup(
    name='ntelebot',
    version='0.2.0.0',
    author='Daniel Reed',
    author_email='nmlorg@gmail.com',
    description='A simple implementation of https://core.telegram.org/bots/api.',
    url='https://github.com/nmlorg/ntelebot',
    packages=setuptools.find_packages(include=('ntelebot', 'ntelebot.*')),
    install_requires=['requests'])
