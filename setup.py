# setup.py
from setuptools import setup, find_packages

setup(
    name="logingest",
    version="0.1.0",
    packages=find_packages(where=".", include=['src', 'src.*']),
    package_dir={"": "."},
    package_data={"src": ["*.yaml"]},
    install_requires=[
        "psycopg2-binary>=2.9.3",
        "pyyaml>=6.0",
        "httpx>=0.23.0",
        "python-dotenv>=0.21.0",
        "python-dateutil>=2.8.2",
        "pydantic>=1.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "black>=22.10.0",
            "isort>=5.10.1",
            "mypy>=0.991",
            "pylint>=2.15.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "logingest=src.main:main",
            "logingest-legacy=src.services.ingestion:main",
        ],
    },
)