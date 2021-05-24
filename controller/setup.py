"""Set up the ImJoy engine controller package."""
import json
from pathlib import Path

from setuptools import find_packages, setup

DESCRIPTION = "ImJoy engine controller for Kubernetes cluster."

ROOT_DIR = Path(__file__).parent.resolve()
README_FILE = ROOT_DIR / "README.md"
LONG_DESCRIPTION = README_FILE.read_text(encoding="utf-8")
VERSION_FILE = ROOT_DIR / "imjoy_app_controller" / "VERSION"
VERSION = json.loads(VERSION_FILE.read_text())["version"]

REQUIRES = ["kubernetes", "imjoy>=0.11.15"]

setup(
    name="imjoy-app-controller",
    version=VERSION,
    url="https://github.com/imjoy-team/imjoy-engine-cluster",
    author="ImJoy-Team",
    author_email="imjoy.team@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license="MIT",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
    install_requires=REQUIRES,
    entry_points={'imjoy_core_server_extension': 'imjoy_app_controller=imjoy_app_controller.__main__:setup_extension'},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet",
    ],
)
