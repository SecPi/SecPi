
from collections import OrderedDict


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
				return val
	
	return val