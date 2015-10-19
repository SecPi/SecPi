#!/usr/bin/env python
import json
import os

conf = {}

def load(path):
	global conf
	try:
		pypath = os.environ['PYTHONPATH']
	except KeyError:
		pypath = ""

	#config_file=os.path.join("..", "config.json")
	#config_file="config.json"
	config_file=os.path.join(os.path.join(pypath, path), "config.json")

	with open(config_file) as data_file:    
		conf = json.load(data_file)



def get(key, default=None):
	return conf.get(key, default)

def set(key, value):
	conf[key] = value

def save():
	with open(config_file, 'w') as outfile:
		json.dump(conf, outfile)

def getDict():
	return conf
