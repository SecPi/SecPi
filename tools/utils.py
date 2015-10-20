
from collections import OrderedDict
import dateutil.parser
import pytz

import json
import datetime

import cherrypy

def filter_fields(fields, filter):
	filtered_data = OrderedDict()
	
	for k,v in fields.iteritems():
		if filter in v['visible']:
			filtered_data[k] = v
	
	return filtered_data
	
def str_to_value(val):
	# print("checking %s: %s\n"%(val, type(val)))
	if(type(val) is str or type(val) is unicode):
		
		if(val=="None"): return None
		if(val.lower()=="true"): return True
		if(val.lower()=="false"): return False
		try:
			return int(val)
		except ValueError:
			try:
				return float(val)
			except ValueError:
				try:
					dat = dateutil.parser.parse(val)
					return dat.replace(tzinfo=None) #pytz.UTC.localize(dat)
				except:
					return val
	
	return val

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