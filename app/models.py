from app import app, db
from flask_user import UserMixin
from datetime import datetime

class Address(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	line1 = db.Column(db.String(100))
	line2 = db.Column(db.String(100))
	city = db.Column(db.String(35))
	state = db.Column(db.String(2))
	zip_code = db.Column(db.String(5))
	food_resource_id = db.Column(db.Integer, db.ForeignKey('food_resource.id'))

class TimeSlot(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	day_of_week = db.Column(db.Integer)
	start_time = db.Column(db.Time)
	end_time = db.Column(db.Time)
	food_resource_id = db.Column(db.Integer, db.ForeignKey('food_resource.id'))

class OpenMonthPair(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	start_month = db.Column(db.Integer)
	end_month = db.Column(db.Integer)
	resource_id = db.Column(db.Integer, db.ForeignKey('food_resource.id'))

class PhoneNumber(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	number = db.Column(db.String(35))
	resource_id = db.Column(db.Integer, db.ForeignKey('food_resource.id'))

class FoodResource(db.Model):
	food_resource_type_enums = ('FARMERS_MARKET','MEALS_ON_WHEELS',
		'FOOD_CUPBOARD','SHARE','SOUP_KITCHEN','WIC_OFFICE')
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(50))
	phone_numbers = db.relationship('PhoneNumber', backref='food_resource', lazy='select', uselist=True)
	url = db.Column(db.Text)
	openmonthpairs = db.relationship('OpenMonthPair', backref='food_resource', lazy='select', uselist=True)
	exceptions = db.Column(db.Text)
	description = db.Column(db.Text)
	location_type = db.Column(db.Enum(*food_resource_type_enums))
	timeslots = db.relationship(
		'TimeSlot', # One-to-many relationship (one Address with many TimeSlots).
		backref='food_resource', # Declare a new property of the TimeSlot class.
		lazy='select', uselist=True)
	address = db.relationship('Address', backref='food_resource', 
		lazy='select', uselist=False)

	def serialize_name_only(self):
		return {
			'id': self.id, 
			'name': self.name
		}

	def serialize_all_data(self):
		return {
			'id': self.id, 
			'name': self.name, 
			'phone_number': self.phone_number, 
			'description': self.description
		}
class Role(db.Model):
	role_type_enums = ('User','Admin')
	id = db.Column(db.Integer(), primary_key=True)
	name = db.Column(db.Enum(*role_type_enums))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class UserRoles(db.Model):
	id = db.Column(db.Integer(), primary_key=True)
	user_id = db.Column(db.Integer(), db.ForeignKey('user.id', 
		ondelete='CASCADE'))
	role_id = db.Column(db.Integer(), db.ForeignKey('role.id', 
		ondelete='CASCADE'))

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)

	# User Authentication information
	password = db.Column(db.String(255), nullable=False, default='')
	reset_password_token = db.Column(db.String(100), nullable=False, default='')

	# User Email information
	email = db.Column(db.String(255), nullable=False, unique=True)
	confirmed_at = db.Column(db.DateTime())

	# User information
	is_enabled = db.Column(db.Boolean(), nullable=False, default=False)
	first_name = db.Column(db.String(50), nullable=False, default='')
	last_name = db.Column(db.String(50), nullable=False, default='')

	roles = db.relationship('Role', secondary='user_roles',
			backref=db.backref('users', lazy='dynamic'))

	def is_active(self):
		return self.is_enabled

	def verify_password(self, attept):
		return app.user_manager.verify_password(attept, self.password)

	# This function is only for the tests in tests.py
	def confirm_and_enable_debug(self):
		self.confirmed_at = datetime.now()
		self.is_enabled = True

	def __init__(self, email, password, is_enabled, first_name = '', last_name = '', roles = [Role(name = 'Admin')]):
		self.email = email
		self.password = app.user_manager.hash_password(password = password)
		self.first_name = first_name
		self.last_name = last_name
		self.roles = roles
		self.is_enabled = is_enabled
