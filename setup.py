# setup.py
from setuptools import setup, find_packages

setup(
    name="distributed-task-system",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "requests",
        "psutil",
        "zeroconf",
        "flask_cors",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "dts-start=dts_cli:main",
        ],
    },
    data_files=[
        ("/etc/systemd/system", ["dts.service"])
    ]
)
