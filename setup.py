from setuptools import setup, find_packages

setup(
    name="alpha-prime",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "yfinance>=0.2.32",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "statsmodels>=0.14.0",
        "fredapi>=0.5.0",
        "google-generativeai>=0.8.0",
        "openai>=1.0.0",
        "financetoolkit>=1.8.0",
        "financedatabase>=2.2.0",
        "openbb>=4.2.1",
        "loguru>=0.7.0",
        "transformers>=4.35.0",
        "torch>=2.0.0",
        "pyinform>=0.2.0"
    ],
    author="Alpha Prime Team",
    description="Senior Macro Algo-Strategist Intelligence Agent",
    python_requires=">=3.9",
)
