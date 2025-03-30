from setuptools import setup, find_packages

setup(
    name="yashaoxen",
    version="1.0.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "python-iptables>=1.0.1",
        "docker>=6.1.3",
        "requests>=2.31.0",
        "psutil>=5.9.8",
        "PyYAML>=6.0.1",
        "click>=8.1.7",
        "rich>=13.7.0",
        "python-dotenv>=1.0.1",
        "schedule>=1.2.1",
        "prometheus-client>=0.19.0",
    ],
    entry_points={
        'console_scripts': [
            'yashaoxen-manager=yashaoxen.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'yashaoxen': ['config/*.json', 'scripts/*'],
    },
    author="oyash01",
    description="Professional EarnApp Management System with Advanced Proxy Support",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/oyash01/YashaoXen",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.8",
) 