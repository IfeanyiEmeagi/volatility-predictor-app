"""This module extracts information from `.env` file so that
AlphaVantage API key can be made available in other parts of the application.
"""

# The os library allows you to communicate with a computer's
# operating system: https://docs.python.org/3/library/os.html
import os

# pydantic used for data validation: https://pydantic-docs.helpmanual.io/
from pydantic import BaseSettings


def return_full_path(filename: str = ".env") -> str:
    """Uses os to return the correct path of the `.env` file."""
    current_directory = os.getcwd()
    full_path = os.path.join(current_directory, filename)
    return full_path


class Settings(BaseSettings):
    """Uses pydantic to define settings for project."""

    alpha_api_key: str
    db_name: str
    model_directory: str

    class Config:
        env_file = return_full_path(".env")


# Create instance of `Settings` class that will be imported
# in lesson notebooks and the other modules for application.
settings = Settings()