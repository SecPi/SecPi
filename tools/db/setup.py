from tools import config

config.load("management")

import database


# db setup start
print "starting db setup"
database.setup()
print "setup done!"
# db setup end
