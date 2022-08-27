import argparse
import dataclasses
import os
import pathlib


@dataclasses.dataclass
class StartupOptions:
    app_config: pathlib.Path
    logging_config: pathlib.Path


def parse_cmd_args() -> StartupOptions:
    parser = argparse.ArgumentParser(description="Run the SecPi worker")
    parser.add_argument("--app-config", dest="app_config", type=pathlib.Path,
                        required=False,
                        help="Path to the `config-worker.json` configuration file")
    parser.add_argument("--logging-config", dest="logging_config", type=pathlib.Path,
                        help="Path to the `logging.conf` configuration file",
                        required=False)

    args = parser.parse_args()

    options = StartupOptions(
        app_config=args.app_config or os.environ.get("SECPI_APP_CONFIG"),
        logging_config=args.logging_config,
    )
    return options
