import abc
import dataclasses
import io
import typing as t
import zipfile


class Action(object):
    def __init__(self, id, params, worker):
        self.id = id
        self.params = params
        self.corrupted = False
        self.worker = worker

    def post_log(self, msg, lvl):
        self.worker.post_log(msg, lvl)

    def post_err(self, msg):
        self.worker.post_err(msg)

    @abc.abstractmethod
    def execute(self):
        """Do some stuff.
        Params is a dict with additional info for the executing actor."""
        return

    @abc.abstractmethod
    def cleanup(self):
        """Cleanup anything you might have started. (e.g. listening on ports etc.)"""
        return


@dataclasses.dataclass
class FileResponse:
    name: str
    payload: t.Union[str, bytes]

    def __post_init__(self):
        if isinstance(self.payload, str):
            self.payload = self.payload.encode("utf-8")


ResponseItem = t.Union[FileResponse]


class ActionResponse:
    def __init__(self):
        self.data: t.List[ResponseItem] = []

    def add(self, item: ResponseItem):
        self.data.append(item)

    @classmethod
    def make_zip(cls, responses: t.List["ActionResponse"]):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="a", compression=zipfile.ZIP_DEFLATED, allowZip64=False) as zip_file:
            for response in responses:
                if response is None:
                    continue
                for item in response.data:
                    zip_file.writestr(item.name, item.payload)
        return zip_file.filelist, zip_buffer.getvalue()
