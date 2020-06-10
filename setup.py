from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="testwise",
    version="0.0.29",
    description="A backtester (backtest helper) for testing my trading strategies.",
    py_modules=["testwise"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires = ['matplotlib',],
    extras_require = {
        "dev" : [
            "pytest>=3.7",
        ],
    },
    url="https://github.com/aticio/testwise",
    author="Özgür Atıcı",
    author_email="aticiozgur@gmail.com",
)