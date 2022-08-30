import cherrypy

from secpi.util.web import json_handler
from tools.db.objects import Alarm

from ..base_webpage import BaseWebPage


class AlarmsPage(BaseWebPage):
    def __init__(self):
        super(AlarmsPage, self).__init__(Alarm)
        self.fields["id"] = {"name": "ID", "visible": ["list"]}
        self.fields["alarmtime"] = {"name": "Alarm Time", "visible": ["list"]}
        self.fields["sensor_id"] = {"name": "Sensor ID", "visible": ["list", "add"], "type": "number"}
        self.fields["ack"] = {"name": "Ack.", "visible": ["list", "add", "update"], "type": "bool"}
        self.fields["message"] = {"name": "Message", "visible": ["list", "add"]}
        # self.fields['active'] = {'name':'Active', 'visible':['list', 'add', 'update']}

    @cherrypy.expose
    def index(self):
        tmpl = self.lookup.get_template("alarms.mako")
        return tmpl.render(page_title="Alarms")

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
    def ack(self):
        if hasattr(cherrypy.request, "json"):
            id = cherrypy.request.json["id"]
            if id:
                obj = self.db.query(Alarm).get(id)
                if obj:
                    obj.ack = True
                    self.db.commit()
                    return {"status": "success", "message": "Acknowledged alarm with id %s" % obj.id}

        return {"status": "error", "message": "ID not found"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
    def ackAll(self):
        les = self.db.query(Alarm).filter(Alarm.ack == 0).all()
        if les:
            for le in les:
                le.ack = True

            self.db.commit()
            return {"status": "success", "message": "Acknowledged all alarms"}

        return {"status": "error", "message": "No alarms to acknowledge found"}
