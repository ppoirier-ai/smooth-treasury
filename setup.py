from setuptools import setup, find_packages

setup(
    name="grid-trading-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "click>=8.0.0",
        "sqlalchemy>=1.4.0",
        "pydantic>=1.8.0",
        "python-binance>=1.0.0",
        "python-telegram-bot>=13.0",
        "pyyaml>=5.4.0",
        "redis>=4.0.0",
        "pika>=1.2.0",  # For RabbitMQ
        "cryptography>=3.4.0",  # For API key encryption
    ],
    entry_points={
        "console_scripts": [
            "gridbot=cli.main:cli",
        ],
    },
) 