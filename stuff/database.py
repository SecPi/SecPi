from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func


# source: http://sqlalchemy.readthedocs.org/en/rel_1_0/orm/tutorial.html

# db setup start
print "starting setup"
engine = create_engine('sqlite:///:memory:', echo = True)

Base = declarative_base()

class User(Base):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True)
	name = Column(String)
	fullname = Column(String)
	password = Column(String)
	
	addresses = relationship("Address", backref='user', cascade="all, delete, delete-orphan")

	def __repr__(self):
		return "<User(name='%s', fullname='%s', password='%s')>" % (self.name, self.fullname, self.password)


class Address(Base):
	__tablename__ = 'addresses'
	id = Column(Integer, primary_key=True)
	email_address = Column(String, nullable=False)
	user_id = Column(Integer, ForeignKey('users.id'))


	def __repr__(self):
		return "<Address(email_address='%s')>" % self.email_address


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

jack = User(name='jack', fullname='Jack Bean', password='gjffdd')
jack.addresses = [
	Address(email_address='jack@google.com'),
	Address(email_address='j25@yahoo.com')]

session.add(jack)
session.commit()

print "jack: "
print jack.addresses[1]
print jack.addresses[1].user


jack = session.query(User).filter_by(name='jack').one()

print "got jack from db:"
print jack
print jack.addresses

# getting by primary id
jack = session.query(User).get(5) 
del jack.addresses[1]

session.delete(jack)
print session.query(User).filter_by(name='jack').count()


print session.query(Address).filter(Address.email_address.in_(['jack@google.com', 'j25@yahoo.com'])).count()





'''
# subquery 
stmt = session.query(Address.user_id, func.count('*').label('address_count')).group_by(Address.user_id).subquery()
for u, count in session.query(User, stmt.c.address_count).outerjoin(stmt, User.id==stmt.c.user_id).order_by(User.id): 
	print u, count


# join with select from two tables
for u, a in session.query(User, Address).filter(User.id==Address.user_id).filter(Address.email_address=='jack@google.com').all():   
	print u
	print a

# normal join
session.query(User).join(Address).filter(Address.email_address=='jack@google.com').all()


# selecting objects
for instance in session.query(User).order_by(User.id): 
	print instance.name, instance.fullname

# selecting values
for name, fullname in session.query(User.name, User.fullname): 
	print name, fullname


# selecting values per row
for row in session.query(User, User.name).all(): 
	print row.User, row.name

# labels for selected values
for row in session.query(User.name.label('name_label')).all(): 
	print(row.name_label)

# getting a subset
for u in session.query(User).order_by(User.id)[1:3]: 
	print u

# filtering
for name, in session.query(User.name).filter_by(fullname='Ed Jones'): 
	print name

# filtering
for name, in session.query(User.name).filter(User.fullname=='Ed Jones'): 
	print name

'''











