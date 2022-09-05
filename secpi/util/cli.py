import argparse
import os
import pathlib

from secpi.model.settings import StartupOptions


def parse_cmd_args() -> StartupOptions:
    parser = argparse.ArgumentParser(description="Run the SecPi worker")
    parser.add_argument(
        "--app-config",
        dest="app_config",
        type=pathlib.Path,
        required=False,
        help="Path to the `config-{manager,worker,web}.toml` configuration file",
    )
    parser.add_argument(
        "--logging-config",
        dest="logging_config",
        type=pathlib.Path,
        help="Path to the `logging.conf` configuration file",
        required=False,
    )
    parser.add_argument("--log-file", dest="log_file", type=pathlib.Path, help="Path to the log file", required=False)

    args = parser.parse_args()

    options = StartupOptions(
        app_config=args.app_config or os.environ.get("SECPI_APP_CONFIG"),
        logging_config=args.logging_config,
        log_file=args.log_file,
    )
    return options
