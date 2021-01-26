from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="mfrc522",
    version="0.0.10",
    author="zachary822",
    description="A library to integrate the MFRC522 RFID readers with the Raspberry Pi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zachary822/MFRC522-python",
    packages=find_packages(exclude=["scripts", "tests"]),
    install_requires=[
        'RPi.GPIO; platform_system=="linux"',
        'spidev; platform_system=="linux"',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Hardware",
    ],
)
