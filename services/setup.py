from setuptools import setup, find_packages

setup(
    name="astra-services",
    version="0.1.0",
    description="ASTRA OS Services Package - compatibility layer",
    python_requires=">=3.12",
    packages=find_packages(include=["services", "services.*"]),
    install_requires=[
        "astra-agent-orchestrator>=0.1.0",
    ],
    package_data={
        "services": ["*.py"],
    },
    zip_safe=False,
)
