from setuptools import setup, find_packages

setup(
    name="fastapi_skeleton",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "pydantic[dotenv]",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "httpx",
        ],
    },
)
