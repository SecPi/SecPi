from tools import config

config.load("manager")

import database
import sys


# db setup start
print "starting db setup"
database.connect(sys.argv[1])
database.setup()
print "setup done!"
# db setup end
