import setuptools


setuptools.setup(
    name='ntelebot',
    version='0.4.1',
    author='Daniel Reed',
    author_email='nmlorg@gmail.com',
    description='A simple implementation of https://core.telegram.org/bots/api.',
    url='https://github.com/nmlorg/ntelebot',
    packages=setuptools.find_packages(include=('ntelebot', 'ntelebot.*')),
    python_requires='>=3.8',
    install_requires=['requests'])
