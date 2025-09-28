"""Application configuration objects."""

import os


class BaseConfig:
    DEBUG = False
    TESTING = False
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    PROPAGATE_EXCEPTIONS = True
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")


class ProductionConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def get_config(name: str):
    name_lower = (name or "development").lower()
    if name_lower.startswith("prod"):
        return ProductionConfig
    return DevelopmentConfig