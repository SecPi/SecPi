from tools import config

config.load("management")

import database


# db setup start
print "starting db setup"
database.connect()
database.setup()
print "setup done!"
# db setup end
