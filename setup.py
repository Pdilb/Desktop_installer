from setuptools import setup, find_packages

setup(
    name="desktop_installer",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["PySide6>=6.5"],
    entry_points={
        "console_scripts": [
            "desktop_installer = desktop_installer.__main__:main",
            "dtier = desktop_installer.__main__:main",
        ],
    },
    python_requires=">=3.10",
)