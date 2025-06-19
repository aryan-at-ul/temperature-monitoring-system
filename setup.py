from setuptools import setup, find_packages

setup(
    name="temperature-monitoring-system",
    version="0.1.0",
    description="Cold‑chain temperature monitoring platform",
    author="Aryan Singh",
    packages=find_packages(exclude=["tests*", "docs*", "data*"]),
    install_requires=[line.strip() for line in open("requirements.txt") if line and not line.startswith("#")],
    python_requires=">=3.9",
)
