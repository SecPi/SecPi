import dataclasses
import pathlib
import typing as t


@dataclasses.dataclass
class StartupOptions:
    app_config: t.Union[pathlib.Path, str]
    logging_config: t.Union[pathlib.Path, str]
    log_file: t.Union[pathlib.Path, str]
