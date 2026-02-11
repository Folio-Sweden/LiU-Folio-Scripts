# -*- coding: utf-8 -*-
"""
Minimal setup-fil för att kunna köra pip install.
"""

from setuptools import setup

setup(
    name="LiU-Folio-Scripts",
    version="1.0",
    description="Paket med skript som körs mot Folio.",
    url="https://github.com/Folio-Sweden/LiU-Folio-Scripts",
    author="Håkan Sundblad",
    author_email="hakan.sundblad@liu.se",
    license="MIT license",
    packages=[
        "automatic_renewals",
        "libris_import",
        "utils",
    ],
    install_requires=[
        "httpx",
        "pyfolioclient>=0.1.7",
        "pymarc",
        "python-dotenv",
    ],
    zip_safe=False,
)
