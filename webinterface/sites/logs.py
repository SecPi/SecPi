import cherrypy

from secpi.util.web import json_handler
from tools.db.objects import LogEntry

from ..base_webpage import BaseWebPage


class LogEntriesPage(BaseWebPage):
    def __init__(self):
        super(LogEntriesPage, self).__init__(LogEntry)
        self.fields["id"] = {"name": "ID", "visible": ["list"]}
        self.fields["logtime"] = {"name": "Time", "visible": ["list", "add"]}
        self.fields["ack"] = {"name": "Ack", "visible": ["list", "add", "update"], "type": "bool"}
        self.fields["level"] = {"name": "Log Level", "visible": ["list", "add"], "type": "number"}
        self.fields["sender"] = {"name": "Sender", "visible": ["list", "add"]}
        self.fields["message"] = {"name": "Message", "visible": ["list", "add"]}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
    def ack(self):
        if hasattr(cherrypy.request, "json"):
            id = cherrypy.request.json["id"]
            if id:
                obj = self.db.query(LogEntry).get(id)
                if obj:
                    obj.ack = True
                    self.db.commit()
                    return {"status": "success", "message": "Acknowledged log message with id %s" % obj.id}

        return {"status": "error", "message": "ID not found"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
    def ackAll(self):
        les = self.db.query(LogEntry).filter(LogEntry.ack == 0).all()
        if les:
            for le in les:
                le.ack = True

            self.db.commit()
            return {"status": "success", "message": "Acknowledged all log messages"}

        return {"status": "error", "message": "No log messages to acknowledge found"}
