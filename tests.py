#!flask/bin/python
import unittest
import os
from datetime import time
from sqlalchemy.exc import IntegrityError
from app import app, db
from config import basedir
from app.models import Address, FoodResource, TimeSlot, User, Role

class TestCase(unittest.TestCase):

    # Run at the beginning of every test.
    def setUp(self):
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
            os.path.join(basedir, 'test.db')
        self.app = app.test_client()
        db.create_all()
        self.create_vars()

    # Run at the end of every test.
    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # Sets up global variables that will be used in several tests.
    def create_vars(self):
        self.a1 = Address(line1 = '1234 MB 1234', line2 = '3700 Spruce St', 
            city = 'Philadelphia', state = 'PA', zip_code = '14109')
        self.a2 = Address(line1 = '4567 MB 1234', line2 = '3600 Spruce St', 
            city = 'Philadelphia', state = 'PA', zip_code = '14109')

        self.timeslots_list = \
            [TimeSlot(day_of_week = 0, start_time = time(8,0), 
                end_time = time(18,30)),
            TimeSlot(day_of_week = 1, start_time = time(7,0), 
                end_time = time(19,30)),
            TimeSlot(day_of_week = 2, start_time = time(7,30), 
                end_time = time(18,30)),
            TimeSlot(day_of_week = 3, start_time = time(8,0), 
                end_time = time(19,30)),
            TimeSlot(day_of_week = 4, start_time = time(10,0), 
                end_time = time(5,30)),
            TimeSlot(day_of_week = 5, start_time = time(8,15), 
                end_time = time(18,45)),
            TimeSlot(day_of_week = 6, start_time = time(9,0), 
                end_time = time(20,45))]

        self.desc = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
            Donec sem neque, vehicula ac nisl at, porta porttitor enim. 
            Suspendisse nibh eros, pulvinar nec risus a, dignissim efficitur 
            diam. Phasellus vestibulum posuere ex, vel hendrerit turpis molestie 
            sit amet. Nullam ornare magna quis urna sodales, vel iaculis purus 
            consequat. Mauris laoreet enim ipsum. Cum sociis natoque penatibus 
            et magnis dis parturient montes, nascetur ridiculus mus. Nulla 
            facilisi. In et dui ante. Morbi elementum dolor ligula, et mollis 
            magna interdum non. Mauris ligula mi, mattis at ex ut, pellentesque 
            porttitor elit. Integer volutpat elementum tristique. Ut interdum, 
            mauris a feugiat euismod, tortor."""

        self.u1 = User(username = 'ben', password = 'pass123', 
            email='ben@ben.com', first_name = 'Ben', last_name = 'Sandler', 
            roles=[Role(name = 'User')])
        self.u2 = User(username = 'steve', password = 'p@$$w0rd', 
            email = 'steve@gmail.com', first_name = 'Steve', 
            last_name = 'Smith', roles = [Role(name = 'User')])
        self.u3 = User(username = 'sarah', 
            password = '139rjf9i#@$#R$#!#!!!48939832984893rfcnj3@#%***^%$#@#$@#', 
            email = 'sarah@gmail.com', first_name = 'Sarah', last_name = 'Smith', 
            roles = [Role(name = 'Admin')])

    # Adds two valid addresses to the database and then checks that both can be 
    # retrieved and that a bad query returns no results.
    def test_writing_reading_address(self):
    	db.session.add(self.a1)
    	db.session.add(self.a2)
    	db.session.commit()
    	assert len(Address.query
            .filter_by(zip_code = '14109').all()) == 2
    	assert len(Address.query
            .filter_by(zip_code = '14109', city = 'New York').all()) == 0

    # Adds a valid Address to the database and then makes sure it can be 
    # retrieved by name and address.
    def test_create_valid_food_resource(self):

        r1 = FoodResource(name = 'Test Food Resource 1', address = self.a1, 
            phone_number = '1234567898', timeslots = self.timeslots_list,
            description = self.desc, location_type = 'FARMERS_MARKET')
        db.session.add(r1)
        db.session.commit()
        assert len(FoodResource.query.filter_by(name = 'Test Food Resource 1')
            .all()) == 1
        assert len(FoodResource.query.filter_by(address = self.a1)
            .all()) == 1
        assert len(FoodResource.query.filter_by(name = 'Test Food Resource 1')
            .first().timeslots) == 7

    # Tries to add an invalid Address to the database (does not use a proper 
    # location_type enum) and ensures IntegrityError is raised.
    def test_create_invalid_food_resource_enum_resource(self):
      self.assertRaises(IntegrityError, 
        r1 = FoodResource(name = 'Test Food Resource 1', address = self.a2,
            phone_number = '1234567898', timeslots = self.timeslots_list, 
            description = self.desc, location_type = 'WRONG_ENUM!!!!!!!!!!!!!'))

    def test_create_user(self):
        db.session.add(self.u1)
        db.session.commit()
        assert len(Role.query.filter_by(name = 'User').all()) == 1
        u = User.query.filter_by(username = 'ben').first()
        assert u
        assert u.verify_password('pass123')
        assert not(u.verify_password('pass124'))

    def test_create_multiple_users(self):
        db.session.add(self.u1)
        db.session.add(self.u2)
        db.session.add(self.u3)
        db.session.commit()
        assert len(Role.query.filter_by(name = 'User').all()) == 2
        assert len(Role.query.filter_by(name = 'Admin').all()) == 1
        assert len(Role.query.filter_by(name = 'N/A').all()) == 0
        u = User.query.filter_by(username = 'sarah').first()
        assert u.verify_password('139rjf9i#@$#R$#!#!!!48939832984893rfcnj3@#%***^%$#@#$@#')
        assert not(u.verify_password('239rjf9i#@$#R$#!#!!!48939832984893rfcnj3@#%***^%$#@#$@#'))

if __name__ == '__main__':
    unittest.main()
