import cherrypy

from secpi.model.dbmodel import Zone

from ..base_webpage import BaseWebPage


class ZonesPage(BaseWebPage):
    def __init__(self):
        super(ZonesPage, self).__init__(Zone)
        self.fields["id"] = {"name": "ID", "visible": ["list"]}
        self.fields["name"] = {"name": "Name", "visible": ["list", "add", "update"]}
        self.fields["description"] = {"name": "Description", "visible": ["list", "add", "update"]}

    @cherrypy.expose
    def index(self):
        tmpl = self.lookup.get_template("zones.mako")
        return tmpl.render(page_title="Zones")
