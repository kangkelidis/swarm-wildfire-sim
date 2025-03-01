from setuptools import find_packages, setup

# Read requirements from requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="wildfire_simulation",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "swarm-wildfire-sim=src.main:main",
        ],
    },
)
