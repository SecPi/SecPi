#!/usr/bin/env python
import config

curstate = config.get("state")
print "curstate: ", curstate
config.set("state", not curstate)
config.save()
print "done"
