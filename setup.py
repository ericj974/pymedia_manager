from setuptools import setup, find_packages

setup(
    name='media-manager',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'myscript = main_app:main',
        ],
    },
)