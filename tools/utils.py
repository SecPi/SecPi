import logging
import pathlib
import sys
from collections import OrderedDict
import dateutil.parser
import netifaces
import pytz

import json
import datetime

import cherrypy

LEVEL_DEBUG=0
LEVEL_INFO=50
LEVEL_WARN=75
LEVEL_ERR=100


EXCHANGE="secpi"
QUEUE_LOG="secpi-log"
QUEUE_DATA="secpi-data"
QUEUE_ALARM="secpi-alarm"
QUEUE_ON_OFF="secpi-on_off"
QUEUE_ACTION="secpi-action-"
QUEUE_CONFIG="secpi-config-"
QUEUE_INIT_CONFIG="secpi-init_config"
QUEUE_OPERATIONAL="secpi-op-"


logger = logging.getLogger(__name__)


def filter_fields(fields, filter):
	filtered_data = OrderedDict()
	
	for k,v in fields.items():
		if filter in v['visible']:
			filtered_data[k] = v
	
	return filtered_data
	
def str_to_value(val):
	# print("checking %s: %s\n"%(val, type(val)))
	if isinstance(val, (str, bytes)):

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

def check_late_arrival(date_message):
		date_now = datetime.datetime.now()

		if (date_now - date_message) < datetime.timedelta(0,30): #TODO: make delta configurable?
			return False
		else:
			return True

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


def setup_logging(level=logging.INFO, config_file=None):
	if config_file:
		config_file = pathlib.Path(config_file)
		if not config_file.exists():
			raise FileNotFoundError(f"Logging configuration file '{config_file}' not found")
		logging.config.fileConfig(config_file, defaults={'logfilename': 'worker.log'})
	else:
		log_format = "%(asctime)-15s [%(name)-34s] %(levelname)-7s: %(message)s"
		logging.basicConfig(format=log_format, stream=sys.stderr, level=level)

	if logging.getLogger().level == logging.DEBUG:
		pika_logger = logging.getLogger("pika")
		pika_logger.setLevel(logging.INFO)


def get_ip_addresses(self):
	"""
	Return the configured ip addresses (v4 & v6) as list.
	"""
	result = []
	# Iterate through interfaces: eth0, eth1, wlan0, etc.
	for interface in netifaces.interfaces():
		if (interface != "lo") and (netifaces.AF_INET in netifaces.ifaddresses(interface)): # filter loopback, and active ipv4
			for ip_address in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
				logger.debug("Adding %s IP to result" % ip_address['addr'])
				result.append(ip_address['addr'])
		if (interface != "lo") and (netifaces.AF_INET6 in netifaces.ifaddresses(interface)): # filter loopback, and active ipv6
			for ipv6_address in netifaces.ifaddresses(interface)[netifaces.AF_INET6]:
				logger.debug("Adding %s IP to result" % ipv6_address['addr'])
				result.append(ipv6_address['addr'])

	return result
