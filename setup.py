"""
Setup script for the quantitative finance data warehouse package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="quant-sql-warehouse",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A production-ready data warehouse for quantitative finance built with DuckDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/quant-sql-warehouse",
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "duckdb>=0.9.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        "python-multipart>=0.0.6",
        "faker>=20.0.0",
        "python-dateutil>=2.8.0",
        "loguru>=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.25.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "isort>=5.12.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "quant-warehouse-generate=etl.generate_data:main",
            "quant-warehouse-load=etl.load_data:main",
            "quant-warehouse-analyze=analytics.run_analysis:main",
            "quant-warehouse-api=api.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.sql", "*.md"],
    },
)

