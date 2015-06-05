
from collections import OrderedDict


def filter_fields(fields, filter):
	filtered_data = OrderedDict()
	
	for k,v in fields.iteritems():
		if filter in v['visible']:
			filtered_data[k] = v
	
	return filtered_data
	
def str_to_value(val):
	if(val=="None"): return None
	if(val=="True"): return True
	if(val=="False"): return False
	try:
		return int(val)
	except ValueError:
		try:
			return float(val)
		except ValueError:
			return val
	return val