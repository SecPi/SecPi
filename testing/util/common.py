import pathlib
import shutil


def clear_directory(path):
    """
    Remove directory contents, but not the directory itself.

    https://stackoverflow.com/a/56151260
    """

    for path in pathlib.Path(path).glob("**/*"):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
