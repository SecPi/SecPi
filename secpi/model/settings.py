import dataclasses
import pathlib


@dataclasses.dataclass
class StartupOptions:
    app_config: pathlib.Path
    logging_config: pathlib.Path
    log_file: pathlib.Path
