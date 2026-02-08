#!/usr/bin/env python3
"""
GitHub Monitor - Setup Configuration
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="github-monitor",
    version="1.0.0",
    author="Socks",
    description="Lightweight GitHub monitoring tool for tracking repository activity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/github-monitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=[
        # Pure stdlib - no external dependencies!
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "github-monitor=monitor:main",
            "github-monitor-check=monitor_check:main",
            "github-monitor-loop=run_monitor_loop:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
