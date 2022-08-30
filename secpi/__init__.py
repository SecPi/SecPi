try:
    from importlib.metadata import PackageNotFoundError, version  # noqa
except ImportError:
    from importlib_metadata import PackageNotFoundError, version  # noqa

try:
    __version__ = version("SecPi")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
