import setuptools


setuptools.setup(
    name='ntelebot',
    version='1.0.0',
    author='Daniel Reed',
    author_email='nmlorg@gmail.com',
    description='A simple implementation of https://core.telegram.org/bots/api.',
    url='https://github.com/nmlorg/ntelebot',
    packages=setuptools.find_packages(include=('ntelebot', 'ntelebot.*')),
    entry_points={'pytest11': ['ntelebot.testing = ntelebot.testing.pytest_plugin']},
    python_requires='>=3.6',
    install_requires=['requests'])
