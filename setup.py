from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="yashaoxen",
    version="1.0.0",
    author="oyash01",
    author_email="charliehackerhack@gmail.com",
    description="Advanced EarnApp Management Tool with Multi-Proxy Support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oyash01/YashaoXen",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "yashaoxen=yashaoxen.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 