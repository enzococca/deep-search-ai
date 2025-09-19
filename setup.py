"""
Setup script per Deep Search AI
"""

from setuptools import setup, find_packages
import os

# Legge il README per la descrizione lunga
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Legge i requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="deep-search-ai",
    version="1.0.0",
    author="Deep Search AI Team",
    author_email="info@deepsearch.ai",
    description="Applicazione avanzata per ricerca intelligente multi-modale con AI GPT-5",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/deep-search-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-flask>=1.3.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
        ],
        "gpu": [
            "torch[cuda]",
            "torchvision[cuda]",
        ],
        "full": [
            "pymilvus>=2.4.0",
            "sentence-transformers>=2.2.0",
            "transformers>=4.40.0",
            "easyocr>=1.7.0",
            "selenium>=4.15.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "deep-search-ai=run:main",
            "deep-search-server=run:run_server",
        ],
    },
    include_package_data=True,
    package_data={
        "app": [
            "static/*",
            "templates/*",
            "config/*.yaml",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/deep-search-ai/issues",
        "Source": "https://github.com/yourusername/deep-search-ai",
        "Documentation": "https://github.com/yourusername/deep-search-ai/wiki",
    },
    keywords=[
        "artificial intelligence",
        "search engine",
        "multimodal search",
        "document analysis",
        "image search",
        "gpt-5",
        "openai",
        "vector database",
        "semantic search",
        "nlp",
        "computer vision",
        "machine learning"
    ],
)
