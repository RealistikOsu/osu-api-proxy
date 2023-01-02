from __future__ import annotations

import os
from dataclasses import dataclass
from dataclasses import field
from json import dump
from json import load
from typing import Any
from typing import get_type_hints
import logging


@dataclass
class Config:
    oapi_key_pool: list[str] = field(default_factory=list)
    app_access_key: str = ""
    http_port: int = 8080
    http_host: str = "0.0.0.0"
    http_prefix: str = "/api"


def read_config_json() -> dict[str, Any]:
    with open("config.json") as f:
        return load(f)


def write_config(config: Config):
    with open("config.json", "w") as f:
        dump(config.__dict__, f, indent=4)


def load_json_config() -> Config:
    """Loads the config from the file, handling config updates.
    Note:
        Raises `SystemExit` on config update.
    """

    config_dict = {}

    if os.path.exists("config.json"):
        config_dict = read_config_json()

    # Compare config json attributes with config class attributes
    missing_keys = [key for key in Config.__annotations__ if key not in config_dict]

    # Remove extra fields
    for key in tuple(
        config_dict,
    ):  # Tuple cast is necessary to create a copy of the keys.
        if key not in Config.__annotations__:
            del config_dict[key]

    # Create config regardless, populating it with missing keys.
    config = Config(**config_dict)

    if missing_keys:
        logging.info(f"Your config has been updated with {len(missing_keys)} new keys.")
        logging.debug("Missing keys: " + ", ".join(missing_keys))
        write_config(config)
        raise SystemExit(0)

    return config


def load_env_config() -> Config:
    conf = Config()

    for key, cast in get_type_hints(conf).items():
        if (env_value := os.environ.get(key.upper())) is not None:
            setattr(conf, key, cast(env_value))

    return conf


def load_config() -> Config:
    if os.environ.get("USE_ENV_CONFIG") == "1":
        return load_env_config()
    return load_json_config()


config = load_config()
