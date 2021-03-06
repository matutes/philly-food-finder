#!flask/bin/python
import unittest
import os
from datetime import time
from sqlalchemy.exc import IntegrityError
from app import app, db
from config import basedir
from app.models import Address, FoodResource, TimeSlot, User, Role, PhoneNumber
from app.utils import *

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
                end_time = time(15,30)),
            TimeSlot(day_of_week = 5, start_time = time(8,15), 
                end_time = time(18,45)),
            TimeSlot(day_of_week = 6, start_time = time(9,0), 
                end_time = time(20,45))]

        self.timeslots_list2 = \
            [TimeSlot(day_of_week = 0, start_time = time(8,0), 
                end_time = time(18,30)),
            TimeSlot(day_of_week = 1, start_time = time(7,0), 
                end_time = time(19,30)),
            TimeSlot(day_of_week = 3, start_time = time(8,0), 
                end_time = time(19,30)),
            TimeSlot(day_of_week = 4, start_time = time(10,0), 
                end_time = time(15,30)),
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

        self.u1 = User(email='ben@ben.com', password = 'pass123', 
            first_name = 'Ben', last_name = 'Sandler', 
            roles=[Role(name = 'User')], is_enabled = True)
        self.u2 = User(email = 'steve@gmail.com', password = 'p@$$w0rd', 
            first_name = 'Steve', last_name = 'Smith', 
            roles = [Role(name = 'User')], is_enabled = True)
        self.u3 = User(email = 'sarah@gmail.com',
            password = '139rjf9i#@$#R$#!#!!!48939832984893rfcnj3@#%***^%$#@#$@#', 
            first_name = 'Sarah', last_name = 'Smith', 
            roles = [Role(name = 'Admin')], is_enabled = True)

        self.p1 = PhoneNumber(number = '1234567898')
        self.p2 = PhoneNumber(number = '9876543215')

    # Adds two valid addresses to the database and then checks that both can be 
    # retrieved and that a bad query returns no results.
    def test_writing_reading_address(self):
    	db.session.add(self.a1)
    	db.session.add(self.a2)
    	db.session.commit()
    	assert len(Address.query.filter_by(zip_code = '14109').all()) == 2
    	assert len(Address.query.filter_by(zip_code = '14109', city = 'New York').all()) == 0

    # Adds a valid Address to the database and then makes sure it can be 
    # retrieved by name and address.
    def test_create_valid_food_resource(self):
        # Create yellow colored pin.
        cp_yellow = ColoredPin(
            color_name="Yellow",
            hex_color="fdd800", 
            pin_image_name="mb_yellow.png"
        )
        db.session.add(cp_yellow)

        # Create farmers' market food resource type.
        frt_farmers_market = FoodResourceType(
            name_singular="Farmers' Market",
            name_plural="Farmers' Markets",
            colored_pin=cp_yellow)
        db.session.add(frt_farmers_market)

        # Create a farmers' market food resource.
        r1 = FoodResource(name = 'Test Food Resource 1', address = self.a1, 
            phone_numbers=[self.p2], timeslots = self.timeslots_list,
            description = self.desc, food_resource_type = frt_farmers_market)
        db.session.add(r1)
        db.session.commit()
        assert len(FoodResource.query.filter_by(name = 'Test Food Resource 1')
            .all()) == 1
        assert len(FoodResource.query.filter_by(address = self.a1)
            .all()) == 1
        assert len(FoodResource.query.filter_by(name = 'Test Food Resource 1')
            .first().timeslots) == 7

    def test_create_user(self):
        db.session.add(self.u1)
        db.session.commit()
        assert len(Role.query.filter_by(name = 'User').all()) == 1
        u = User.query.filter_by(email = 'ben@ben.com').first()
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
        u = User.query.filter_by(email = 'sarah@gmail.com').first()
        assert u.verify_password('139rjf9i#@$#R$#!#!!!48939832984893rfcnj3@#%***^%$#@#$@#')
        assert not(u.verify_password('239rjf9i#@$#R$#!#!!!48939832984893rfcnj3@#%***^%$#@#$@#'))

    def test_is_open(self):
        # Create yellow colored pin.
        cp_yellow = ColoredPin(
            color_name="Yellow",
            hex_color="fdd800", 
            pin_image_name="mb_yellow.png"
        )
        db.session.add(cp_yellow)

        # Create farmers' market food resource type.
        frt_farmers_market = FoodResourceType(
            name_singular="Farmers' Market",
            name_plural="Farmers' Markets",
            colored_pin=cp_yellow)
        db.session.add(frt_farmers_market)

        open_pairs = \
            [OpenMonthPair(start_month = 1, end_month = 3), 
             OpenMonthPair(start_month = 5, end_month = 7),
             OpenMonthPair(start_month = 10, end_month = 11)]

        r1 = FoodResource(name = 'Test Food Resource 1', address = self.a1, 
            phone_numbers=[self.p2], timeslots = self.timeslots_list,
            description = self.desc, food_resource_type = frt_farmers_market
            )
        r2 = FoodResource(name = 'Test Food Resource 1', address = self.a1, 
            phone_numbers=[self.p2], timeslots = self.timeslots_list2,
            description = self.desc, food_resource_type = frt_farmers_market
            )

        r1.open_month_pairs.append(OpenMonthPair(start_month = 1, end_month = 3))
        r1.open_month_pairs.append(OpenMonthPair(start_month = 5, end_month = 7))
        r1.open_month_pairs.append(OpenMonthPair(start_month = 10, end_month = 11))
        r2.open_month_pairs.append(OpenMonthPair(start_month = 1, end_month = 3))
        r2.open_month_pairs.append(OpenMonthPair(start_month = 5, end_month = 7))
        r2.open_month_pairs.append(OpenMonthPair(start_month = 10, end_month = 11))

        # Right month right time
        assert is_open(resource = r1, 
            current_date = datetime(year = 2014, month = 11, day = 24, hour = 12, minute = 30))
        assert is_open(resource = r1, 
            current_date = datetime(year = 2014, month = 2, day = 24, hour = 10, minute = 31))

        # Wrong month wrong time
        assert not is_open(resource = r1, 
            current_date = datetime(year = 2014, month = 9, day = 13, hour = 21, minute = 30))

        # Wrong month right time
        assert not is_open(resource = r1, 
            current_date = datetime(year = 2014, month = 9, day = 13, hour = 10, minute = 22))

        # Right month wrong time
        assert not is_open(resource = r1, 
            current_date = datetime(year = 2014, month = 2, day = 13, hour = 21, minute = 30))

        # Right month, closed on Tuesdays
        assert not is_open(resource = r2, 
            current_date = datetime(year = 2014, month = 11, day = 25, hour = 10, minute = 30))

if __name__ == '__main__':
    unittest.main()
