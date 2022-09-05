from pathlib import Path

import tomlkit


def test_configuration_files():
    """
    Verify that all configuration files are valid JSON.
    """
    config_files = list(Path("./etc").rglob("*.toml"))
    assert len(config_files) >= 9
    for config_file in config_files:
        with open(config_file, "r") as f:
            tomlkit.load(f)
