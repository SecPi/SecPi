#!/usr/bin/env python
import json

config_file="config.json"

with open(config_file) as data_file:    
	conf = json.load(data_file)

def get(key):
	return conf[key]

def set(key, value):
	conf[key] = value

def save():
	with open(config_file, 'w') as outfile:
		json.dump(conf, outfile)
