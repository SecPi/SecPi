import cherrypy

from tools.db.objects import Notifier

from ..base_webpage import BaseWebPage


class NotifiersPage(BaseWebPage):
    def __init__(self):
        super(NotifiersPage, self).__init__(Notifier)
        self.fields["id"] = {"name": "ID", "visible": ["list"]}
        self.fields["name"] = {"name": "Name", "visible": ["list", "add", "update"]}
        self.fields["description"] = {"name": "Description", "visible": ["list", "add", "update"]}
        self.fields["cl"] = {"name": "Class", "visible": ["list", "add", "update"]}
        self.fields["module"] = {"name": "Module", "visible": ["list", "add", "update"]}
        self.fields["active_state"] = {"name": "Active", "visible": ["list", "add", "update"], "type": "bool"}

    @cherrypy.expose
    def index(self):
        tmpl = self.lookup.get_template("notifiers.mako")
        return tmpl.render(page_title="Notifiers")
