import cherrypy

from tools.db.objects import Setup

from ..base_webpage import BaseWebPage


class SetupsPage(BaseWebPage):
    def __init__(self):
        super(SetupsPage, self).__init__(Setup)
        self.fields["id"] = {"name": "ID", "visible": ["list"]}
        self.fields["name"] = {"name": "Name", "visible": ["list", "add", "update"]}
        self.fields["description"] = {"name": "Description", "visible": ["list", "add", "update"]}
        self.fields["active_state"] = {"name": "Active", "visible": ["list"], "type": "bool"}

    @cherrypy.expose
    def index(self):
        tmpl = self.lookup.get_template("setups.mako")
        return tmpl.render(page_title="Setups")
