from setuptools import setup, find_packages

setup(
    name="mud",                # The package name
    version="0.1",             # Version of the package
    packages=["mud"],  # Automatically finds all packages (like `mud/`)
    include_package_data=True, # Ensures non-code files are included
    install_requires=[         # Dependencies
        "requests"
    ],
)