#!/usr/bin/env python
import json
import logging
import os
import sys

conf = {}

def load(path):
	logging.info(f"Loading configuration from {path}")
	global conf
	
	with open(path) as data_file:    
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
