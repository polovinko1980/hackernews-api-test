"""Pytest configuration and fixtures."""

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import yaml
from dotenv import load_dotenv

from utils.hackernews_api import HackerNewsAPI

# Load environment variables
load_dotenv()


class Config:
    """Simple config object with attribute access."""

    def __init__(self, data: dict[str, Any]):
        for key, value in data.items():
            setattr(self, key, value)


@pytest.fixture(scope="session")
def config() -> dict[str, Any]:
    """Load configuration from YAML based on ENV environment variable.

    Returns:
        Configuration dictionary for the specified environment
    """
    env = os.getenv("ENV", "STAGE").upper()

    config_path = Path(__file__).parent / "config" / "config.yaml"

    with open(config_path) as file:
        config_data = yaml.safe_load(file)

    if env not in config_data:
        available_envs = list(config_data.keys())
        raise ValueError(
            f"Environment '{env}' not found in config. Available: {available_envs}"
        )

    return config_data[env]


@pytest.fixture(scope="session")
def hackernews_api(config: dict[str, Any]) -> Generator[HackerNewsAPI, None, None]:
    """Provide session-scoped HackerNews API client.

    Args:
        config: Config fixture

    Yields:
        HackerNewsAPI instance
    """
    config_obj = Config(config)
    api_client = HackerNewsAPI(config=config_obj)
    yield api_client
    api_client.close()
