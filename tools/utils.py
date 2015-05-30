
from collections import OrderedDict


def filter_fields(fields, filter):
	filtered_data = OrderedDict()
	
	for k,v in fields.iteritems():
		if filter in v['visible']:
			filtered_data[k] = v
	
	return filtered_data