#!/usr/bin/env python
import json
import logging
import pathlib
import typing as t

logger = logging.getLogger(__name__)

conf = {}


def load(path):
    logging.info(f"Loading configuration from {path}")
    global conf

    with open(path) as data_file:
        conf = json.load(data_file)


def get(key, default=None):
    return conf.get(key, default)


def set(key, value):
    conf[key] = value


def save():
    with open(config_file, 'w') as outfile:
        json.dump(conf, outfile)


def getDict():
    return conf


class ApplicationConfig:
    ERROR_FILE_MISSING = "Path to configuration file missing. " \
                         "Either specify command line argument --app-config, or environment variable SECPI_APP_CONFIG"

    def __init__(self, filepath: t.Union[pathlib.Path, str]):
        self.filepath = filepath
        self.config = None
        self.load()

    def load(self):
        if self.filepath is None:
            raise FileNotFoundError(self.ERROR_FILE_MISSING)
        logger.info(f"Loading configuration from {self.filepath}")
        with open(self.filepath, "r") as config_file:
            self.config = json.load(config_file)

    def save(self):
        if self.filepath is None:
            raise FileNotFoundError(self.ERROR_FILE_MISSING)
        logger.info(f"Saving configuration to {self.filepath}")
        with open(self.filepath, "w") as config_file:
            json.dump(self.config, fp=config_file, indent=2)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def update(self, new_config):
        self.config = new_config

    def asdict(self):
        return dict(self.config)
