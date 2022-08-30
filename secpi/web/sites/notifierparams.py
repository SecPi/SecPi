from secpi.model.dbmodel import Param

from ..base_webpage import BaseWebPage


class NotifierParamsPage(BaseWebPage):
    def __init__(self):
        super(NotifierParamsPage, self).__init__(Param)
        self.fields["id"] = {"name": "ID", "visible": ["list"]}
        self.fields["object_id"] = {
            "name": "Notifier ID",
            "visible": ["list", "add", "update"],
            "type": "number",
            "default": 0,
        }
        self.fields["object_type"] = {
            "name": "Type",
            "visible": ["list", "add", "update"],
            "type": "hidden",
            "default": "notifier",
        }
        self.fields["key"] = {"name": "Key", "visible": ["list", "add", "update"]}
        self.fields["value"] = {"name": "Value", "visible": ["list", "add", "update"]}
        self.fields["description"] = {"name": "Description", "visible": ["list", "add", "update"]}