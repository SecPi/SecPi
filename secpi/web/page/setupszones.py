from secpi.model.dbmodel import Setup, Zone

from .baserelationshippage import BaseRelationshipPage


class SetupsZonesPage(BaseRelationshipPage):
    def __init__(self):
        super().__init__(Setup, "setup", Zone, "zone")
