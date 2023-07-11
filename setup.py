from setuptools import setup, find_packages

setup(
    name="pe",
    version="1.0.0",
    packages=find_packages(),
    py_modules=["runner/experiment"],
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "experiment = pe.runner.experiment:experiment"
        ]
    }
)