from setuptools import setup, find_packages

VERSION = "0.0.1"
DESCRIPTION = "AlgoAPI"
LONG_DESCRIPTION = "Python project for Forexconnect API from FXCM"

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="algoapi",
    version=VERSION,
    author="Krishna Khatiwada",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=["forexconnect", "python-dotenv"],
)
