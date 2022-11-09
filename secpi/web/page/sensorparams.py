from secpi.model.dbmodel import Param

from ..base_webpage import BaseWebPage


class SensorParamsPage(BaseWebPage):
    def __init__(self):
        super().__init__(Param)
        self.fields["id"] = {"name": "ID", "visible": ["list"]}
        self.fields["sensor_id"] = {
            "name": "Sensor ID",
            "visible": ["list", "add", "update"],
            "type": "number",
            "default": 0,
        }
        self.fields["object_type"] = {
            "name": "Type",
            "visible": ["list", "add", "update"],
            "type": "hidden",
            "default": "sensor",
        }
        self.fields["key"] = {"name": "Key", "visible": ["list", "add", "update"]}
        self.fields["value"] = {"name": "Value", "visible": ["list", "add", "update"]}
        self.fields["description"] = {"name": "Description", "visible": ["list", "add", "update"]}
