from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker


# db setup start
print "starting setup"
engine = create_engine('sqlite:///:memory:')

Base = declarative_base()

class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True)
	name = Column(String)
	fullname = Column(String)
	password = Column(String)

	def __repr__(self):
		return "<User(name='%s', fullname='%s', password='%s')>" % (self.name, self.fullname, self.password)


Base.metadata.create_all(engine)
print "setup done!"
# db setup end

# create session
Session = sessionmaker(bind=engine)
session = Session()

print "creating user"
ed_user = User(name='ed', fullname='Ed Jones', password='edspassword')
session.add(ed_user)

print ed_user

print "getting user"
our_user = session.query(User).filter_by(name='ed').first()

print our_user


session.add_all([
	User(name='wendy', fullname='Wendy Williams', password='foobar'),
	User(name='mary', fullname='Mary Contrary', password='xxg527'),
	User(name='fred', fullname='Fred Flinstone', password='blah')])

ed_user.password = 'f8s7ccs'

print "dirty:"
print session.dirty
print "new:"
print session.new

session.commit()

print "ed's id: %i" % ed_user.id