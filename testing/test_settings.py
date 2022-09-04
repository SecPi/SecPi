import json
from pathlib import Path


def test_configuration_files():
    """
    Verify that all configuration files are valid JSON.
    """
    json_files = list(Path("./etc").rglob("*.json"))
    assert len(json_files) >= 9
    for json_file in json_files:
        with open(json_file, "r") as f:
            json.load(f)
