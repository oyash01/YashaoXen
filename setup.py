from setuptools import setup, find_packages

setup(
    name="yashaoxen",
    version="1.0.0",
    description="EarnApp container manager with improved error handling and logging",
    author="oyash01",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "docker>=6.0.0",
        "rich>=10.0.0",
        "requests>=2.26.0",
        "python-dotenv>=0.19.0"
    ],
    entry_points={
        "console_scripts": [
            "yashaoxen=src.cli:cli"
        ]
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
) 