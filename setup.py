from setuptools import setup, find_packages

setup(
    name="mud-aw.py",  # Use the registered name on PyPI
    version="0.1.3",
    description="Python API for interacting with MUD Autonomous Worlds",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Nico Rodriguez",
    url="https://github.com/officialnico/mud-aw.py",  # Update the URL to match your project name on GitHub
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
        "web3",
        "pathlib",
        "json",
        "dotenv",
        "typing",
        "pandas",
        "IPython",
        "logging",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
