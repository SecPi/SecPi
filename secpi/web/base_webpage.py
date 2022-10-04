from collections import OrderedDict

import cherrypy
from sqlalchemy import text

from secpi.util.common import str_to_value
from secpi.util.web import json_handler


class BaseWebPage:
    """A baseclass for a CherryPy web page."""

    def __init__(self, baseclass):
        self.baseclass = baseclass
        self.fields = OrderedDict()

    def objectToDict(self, obj):
        data = {}

        for k in self.fields.keys():
            data[k] = obj.__dict__[k]

        return data

    def objectsToList(self, objs):
        data = []

        for o in objs:
            data.append(self.objectToDict(o))

        return data

    @property
    def db(self):
        return cherrypy.request.db

    @property
    def lookup(self):
        return cherrypy.request.lookup

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
    def fieldList(self):
        return {"status": "success", "data": self.fields}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
    def list(self):
        if hasattr(cherrypy.request, "json"):
            qry = self.db.query(self.baseclass)

            if "filter" in cherrypy.request.json and cherrypy.request.json["filter"] != "":
                qry = qry.filter(text(cherrypy.request.json["filter"]))

            if "sort" in cherrypy.request.json and cherrypy.request.json["sort"] != "":
                qry = qry.order_by(text(cherrypy.request.json["sort"]))

            objects = qry.all()

        else:
            objects = self.db.query(self.baseclass).all()

        return {"status": "success", "data": self.objectsToList(objects)}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
    def delete(self):
        if hasattr(cherrypy.request, "json"):
            identifier = cherrypy.request.json["id"]
            if identifier:
                obj = self.db.query(self.baseclass).get(identifier)
                if obj:
                    self.db.delete(obj)
                    self.db.commit()
                    return {"status": "success", "message": "Object deleted"}

        return {"status": "error", "message": "ID not found"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
    def add(self):
        if hasattr(cherrypy.request, "json"):
            data = cherrypy.request.json

            if data and len(data) > 0:
                cherrypy.log("got something %s" % data)
                newObj = self.baseclass()

                for k, v in data.items():
                    if not k == "id":
                        setattr(newObj, k, str_to_value(v))

                self.db.add(newObj)
                self.db.commit()
                return {"status": "success", "message": "Added new object with id %i" % newObj.identifier}

        return {"status": "error", "message": "No data received"}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out(handler=json_handler)
    def update(self):
        if hasattr(cherrypy.request, "json"):
            data = cherrypy.request.json

            identifier = data["id"]

            # check for valid id
            if identifier and identifier > 0:

                if data and len(data) > 0:
                    cherrypy.log("update something %s" % data)
                    obj = self.db.query(self.baseclass).get(identifier)

                    for k, v in data.items():
                        if not k == "id":  # and v is not None --> can be null!?
                            setattr(obj, k, str_to_value(v))

                    self.db.commit()

                    return {"status": "success", "message": "Updated object with id %i" % obj.identifier}

            else:
                return {"status": "error", "message": "Invalid ID"}

        return {"status": "error", "message": "No data received"}
