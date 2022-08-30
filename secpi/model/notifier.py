import abc


class Notifier(object):
    def __init__(self, id, params):
        self.id = id
        self.params = params
        self.corrupted = False

    @abc.abstractmethod
    def notify(self, info):
        return

    @abc.abstractmethod
    def cleanup(self):
        return
