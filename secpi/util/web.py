import datetime
import json

import cherrypy


class SpecialJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return json.JSONEncoder.default(obj)


json_encoder = SpecialJSONEncoder()


def json_handler(*args, **kwargs):
    # Adapted from cherrypy/lib/jsontools.py
    value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
    return json_encoder.iterencode(value)


def jsonify_error(self, status, message, traceback, version):
    """
    Make CherryPy return errors in JSON format.

    https://stackoverflow.com/a/58099906
    """
    response = cherrypy.response
    response.headers["Content-Type"] = "application/json"
    return json.dumps(
        dict(
            status="error",
            message=status,
            description=message,
        ),
        indent=2,
    )
