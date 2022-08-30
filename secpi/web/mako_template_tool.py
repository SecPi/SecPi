import cherrypy
from mako.lookup import TemplateLookup
from mako.template import Template


class MakoTemplateTool(cherrypy.Tool):
    def __init__(self, path):
        self.lookup = TemplateLookup(directories=[path], strict_undefined=True)

        cherrypy.Tool.__init__(self, "on_start_resource", self.bind_lookup, priority=1)

    def bind_lookup(self):
        # cherrypy.engine.publish('mako.get_lookup', self.lookup)
        # cherrypy.log("found lookup %s"%self.lookup)
        cherrypy.request.lookup = self.lookup
