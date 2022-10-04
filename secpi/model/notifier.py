import abc


class Notifier:
    def __init__(self, identifier, params):
        self.identifier = identifier
        self.params = params
        self.corrupted = False

    @abc.abstractmethod
    def notify(self, info):
        return

    @abc.abstractmethod
    def cleanup(self):
        return
