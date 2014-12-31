from app import app, db, utils
from utils import *
from models import *
from forms import *
from flask import render_template, flash, redirect, session, url_for, request, \
	g, jsonify, current_app
from flask.ext.login import login_user, logout_user, current_user, \
	login_required
from variables import *
from datetime import time
from utils import generate_password
from flask_user import login_required, signals
from flask_user.views import _endpoint_url, _send_registered_email
from flask_login import current_user, login_user, logout_user

@app.route('/')
def index():
	return render_template('base.html')

@app.route('/new', methods=['GET', 'POST'])
@app.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def new(id=None):
	form = AddNewFoodResourceForm(request.form)

	# Set timeslot choices.
	for timeslots in form.daily_timeslots:
		for timeslot in timeslots.timeslots:
			timeslot.starts_at.choices=get_possible_opening_times()
			timeslot.ends_at.choices=get_possible_closing_times()

	# Set food resource type choices.
	food_resource_types = FoodResourceType.query \
		.order_by(FoodResourceType.name_plural).all()
	food_resource_types_choices = []
	for food_resource_type in food_resource_types:
		food_resource_types_choices.append(
			(food_resource_type.enum, 
			food_resource_type.name_singular)
		)
	form.location_type.choices = food_resource_types_choices

	# Create a new food resource. 
	if id is None:
		title = "Add New Food Resource"
		food_resource_type = food_resource_types_choices[0][0]
	# Edit an existing food resource.
	else:
		title = "Edit Food Resource"

	# GET request.
	if request.method == 'GET' and id is not None:

		# Populate form with information about existing food resource. 
		food_resource = FoodResource.query.filter_by(id=id).first()
		if food_resource is None:
			return render_template('404.html')

		# Data that can be directly retrieved from the database.
		form.name.data = food_resource.name
		form.location_type.data = food_resource.location_type
		form.address_line1.data = food_resource.address.line1
		form.address_line2.data = food_resource.address.line2
		form.address_city.data = food_resource.address.city
		form.address_state.data = food_resource.address.state
		form.address_zip_code.data = food_resource.address.zip_code
		form.phone_number.data = food_resource.phone_numbers[0].number
		form.website.data = food_resource.url
		form.additional_information.data = food_resource.description
		form.is_for_family_and_children.data = \
			food_resource.is_for_family_and_children
		form.is_for_seniors.data = food_resource.is_for_seniors
		form.is_wheelchair_accessible.data = \
			food_resource.is_wheelchair_accessible
		form.is_accepts_snap.data = food_resource.is_accepts_snap
		form.location_type.data = food_resource.food_resource_type.enum

		# Data that must be interpreted before being rendered.
		if food_resource.are_hours_available == True:
			form.are_hours_available.data = "yes"
		else:
			form.are_hours_available.data = "no"

		for timeslot in food_resource.timeslots:
			index = timeslot.day_of_week
			start_time = timeslot.start_time
			end_time = timeslot.end_time
			form.daily_timeslots[index].timeslots[0].starts_at.data = \
				start_time.strftime("%H:%M")
			form.daily_timeslots[index].timeslots[0].ends_at.data = \
				end_time.strftime("%H:%M")
			form.is_open[index].is_open.data = "open"

	# POST request.
	additional_errors = []
	if request.method == 'POST' and form.validate(): 
		food_resource_type = form.location_type.data
		all_timeslots = []

		if form.are_hours_available.data == "yes":
			are_hours_available = True
		else:
			are_hours_available = False

		# Create the food resource's timeslots.
		are_timeslots_valid = True
		if are_hours_available: 
			for i, timeslots in enumerate(form.daily_timeslots):
				for timeslot in timeslots.timeslots:
					# Check if food resource is open on the i-th day of the 
					# week.
					is_open = True
					if form.is_open[i].is_open.data == "closed":
						is_open = False

					# Create timeslots only if the food resource is open on the
					# i-th day of the week.
					if is_open:
						start_time = \
							get_time_from_string(timeslot.starts_at.data)
						end_time = get_time_from_string(timeslot.ends_at.data)
						timeslot = TimeSlot(day_of_week=i, 
							start_time=start_time, end_time=end_time)
						all_timeslots.append(timeslot)

						# Check that timeslot is valid.
						if start_time >= end_time: 
							are_timeslots_valid = False
							additional_errors.append("Opening time must be \
								before closing time.")
						else:
							db.session.add(timeslot)

		# Create the food resource's remaining attributes. 
		if are_timeslots_valid:

			# If editing an existing food resource, delete its current record
			# from the database. 
			if id is not None:
				fr = FoodResource.query.filter_by(id=id).first()
				if fr:
					db.session.delete(fr)
					db.session.commit()

			# Create food resource's address.
			address = Address(line1=form.address_line1.data, 
				line2=form.address_line2.data, 
				city=form.address_city.data, 
				state=form.address_state.data, 
				zip_code=form.address_zip_code.data)
			db.session.add(address)

			# Create food resource's phone number.
			phone_numbers = []
			home_number = PhoneNumber(number=form.phone_number.data)
			db.session.add(home_number)
			phone_numbers.append(home_number)

			# Create food resource's type.
			enum = form.location_type.data
			food_resource_type = FoodResourceType.query.filter_by(enum=enum) \
				.first()

			# Create food resource and store all data in it.
			food_resource = FoodResource(
				name=form.name.data, 
				phone_numbers=phone_numbers,
				description=form.additional_information.data,
				timeslots=all_timeslots,
				address=address, 
				is_for_family_and_children = \
					form.is_for_family_and_children.data,
				is_for_seniors = form.is_for_seniors.data,
				is_wheelchair_accessible = form.is_wheelchair_accessible.data,	
				is_accepts_snap = form.is_accepts_snap.data, 
				are_hours_available = are_hours_available,
				food_resource_type = food_resource_type)

			# Commit all database changes. 
			db.session.add(food_resource)
			db.session.commit()
			return redirect(url_for('admin'))

	# If GET request is received or POST request fails due to invalid timeslots, 
	# render the page. 
	return render_template('add_resource.html', form=form, 
		days_of_week=days_of_week,  
		additional_errors=additional_errors, title=title)

#Allows non-admins to add food resources
@app.route('/propose-resource', methods=['GET', 'POST'])
def guest_new_food_resource():
	form = NonAdminAddNewFoodResourceForm(request.form)

	# Set timeslot choices.
	for timeslots in form.daily_timeslots:
		for timeslot in timeslots.timeslots:
			timeslot.starts_at.choices=get_possible_opening_times()
			timeslot.ends_at.choices=get_possible_closing_times()

	# Set food resource type choices.
	food_resource_types = FoodResourceType.query \
		.order_by(FoodResourceType.name_plural).all()
	food_resource_types_choices = []
	for food_resource_type in food_resource_types:
		food_resource_types_choices.append(
			(food_resource_type.enum, 
			food_resource_type.name_singular)
		)
	form.location_type.choices = food_resource_types_choices

	# Initialize location type.
	if request.method == 'GET':
		form.location_type.data = food_resource_types_choices[0][0]

	additional_errors = []
	if request.method == 'POST' and form.validate(): 
		# Check if this guest has added resources in the past. If not,
		# create a new FoodResourceContact.
		guest_name = form.your_name.data
		guest_email = form.your_email_address.data
		guest_phone_number = form.your_phone_number.data

		# Check to see if this contact exists.
		contact = FoodResourceContact.query.filter_by(
			email = guest_email, name = guest_name).first()

		if (contact is None):
			contact = FoodResourceContact(name=guest_name, 
				email=guest_email, phone_number=guest_phone_number)
			db.session.add(contact)
			db.session.commit()

		if form.are_hours_available.data == "yes":
			are_hours_available = True
		else:
			are_hours_available = False

		# Create the food resource's timeslots.
		are_timeslots_valid = True
		all_timeslots = []
		if are_hours_available: 
			for i, timeslots in enumerate(form.daily_timeslots):
				for timeslot in timeslots.timeslots:

					# Check if food resource is open on the i-th day of the 
					# week.
					is_open = True
					if form.is_open[i].is_open.data == "closed":
						is_open = False

					# Create timeslots only if the food resource is open on the
					# i-th day of the week.
					if is_open:
						start_time = \
							get_time_from_string(timeslot.starts_at.data)
						end_time = get_time_from_string(timeslot.ends_at.data)
						timeslot = TimeSlot(day_of_week=i, 
							start_time=start_time, end_time=end_time)
						all_timeslots.append(timeslot)

						# Check that timeslot is valid.
						if start_time >= end_time: 
							are_timeslots_valid = False
							additional_errors.append("Opening time must be \
								before closing time.")
						else:
							db.session.add(timeslot)

		# Create the food resource's remaining attributes. 
		if are_timeslots_valid:

			# Create food resource's address.
			address = Address(line1 = form.address_line1.data, 
				line2 = form.address_line2.data, 
				city = form.address_city.data, 
				state = form.address_state.data, 
				zip_code = form.address_zip_code.data)
			db.session.add(address)

			# Create food resource's phone number.
			phone_numbers = []
			home_number = PhoneNumber(number = form.phone_number.data)
			db.session.add(home_number)
			phone_numbers.append(home_number)

			# Create food resource's type.
			enum = form.location_type.data
			print enum
			food_resource_type = FoodResourceType.query.filter_by(enum=enum) \
				.first()
			print food_resource_type.name_singular

			# Create food resource and store all data in it.
			food_resource = FoodResource(
				name=form.name.data, 
				phone_numbers=phone_numbers,
				description=form.additional_information.data,
				timeslots=all_timeslots,
				address=address, 
				is_for_family_and_children = \
					form.is_for_family_and_children.data,
				is_for_seniors = form.is_for_seniors.data,
				is_wheelchair_accessible = form.is_wheelchair_accessible.data,	
				is_accepts_snap = form.is_accepts_snap.data, 
				are_hours_available = are_hours_available, 
				food_resource_type = food_resource_type, 
				is_approved = False, 
				food_resource_contact = contact)

			# Commit all database changes. 
			db.session.add(food_resource)
			db.session.commit()
			return redirect(url_for('post_guest_add'))

	# If GET request is received or POST request fails due to invalid timeslots, 
	# render the page. 
	return render_template('guest_add_resource.html', form=form, 
		days_of_week=days_of_week,  
		additional_errors=additional_errors)

@app.route('/_thank-you')
def post_guest_add():
	return render_template('thank_you.html')

@app.route('/admin/manage-resources')
@login_required
def admin():
	food_resource_types = FoodResourceType.query \
		.order_by(FoodResourceType.name_plural).all()

	contacts = FoodResourceContact.query.all()

	return render_template('admin_resources.html', 
		food_resource_contacts=contacts, 
		days_of_week=days_of_week,
		food_resource_types=food_resource_types)

@app.route('/admin')
def admin_redirect():
	return redirect(url_for('admin'))

@login_required
def invite():
	""" Display invite form and create new User."""
	user_manager =  current_app.user_manager
	db_adapter = user_manager.db_adapter

	next = request.args.get('next', _endpoint_url(user_manager.after_login_endpoint))
	reg_next = request.args.get('reg_next', _endpoint_url(user_manager.after_register_endpoint))

	login_form = user_manager.login_form()                      
	register_form = user_manager.register_form(request.form)   

	if request.method!='POST':
		login_form.next.data     = register_form.next.data     = next
		login_form.reg_next.data = register_form.reg_next.data = reg_next

	# Process valid POST
	if request.method=='POST' and register_form.validate():

		User = db_adapter.UserClass
		user_class_fields = User.__dict__
		user_fields = {}

		if db_adapter.UserEmailClass:
			UserEmail = db_adapter.UserEmailClass
			user_email_class_fields = UserEmail.__dict__
			user_email_fields = {}

		if db_adapter.UserAuthClass:
			UserAuth = db_adapter.UserAuthClass
			user_auth_class_fields = UserAuth.__dict__
			user_auth_fields = {}

		# Enable user account
		if db_adapter.UserProfileClass:
			if hasattr(db_adapter.UserProfileClass, 'active'):
				user_auth_fields['active'] = True
			elif hasattr(db_adapter.UserProfileClass, 'is_enabled'):
				user_auth_fields['is_enabled'] = True
			else:
				user_auth_fields['is_active'] = True
		else:
			if hasattr(db_adapter.UserClass, 'active'):
				user_fields['active'] = True
			elif hasattr(db_adapter.UserClass, 'is_enabled'):
				user_fields['is_enabled'] = True
			else:
				user_fields['is_active'] = True

		# For all form fields
		for field_name, field_value in register_form.data.items():	
			# Store corresponding Form fields into the User object and/or UserProfile object
			if field_name in user_class_fields:
				user_fields[field_name] = field_value
			if db_adapter.UserEmailClass:
				if field_name in user_email_class_fields:
					user_email_fields[field_name] = field_value
			if db_adapter.UserAuthClass:
				if field_name in user_auth_class_fields:
					user_auth_fields[field_name] = field_value

		# Generates temporary password
		password = generate_password(9)
		if db_adapter.UserAuthClass:
			user_auth_fields['password'] = password
		else:
			user_fields['password'] = password

		g.temp_password = password

		# Add User record using named arguments 'user_fields'
		user = db_adapter.add_object(User, **user_fields)
		if db_adapter.UserProfileClass:
			user_profile = user

		# Add UserEmail record using named arguments 'user_email_fields'
		if db_adapter.UserEmailClass:
			user_email = db_adapter.add_object(UserEmail,
					user=user,
					is_primary=True,
					**user_email_fields)
		else:
			user_email = None

		# Add UserAuth record using named arguments 'user_auth_fields'
		if db_adapter.UserAuthClass:
			user_auth = db_adapter.add_object(UserAuth, **user_auth_fields)
			if db_adapter.UserProfileClass:
				user = user_auth
			else:
				user.user_auth = user_auth
		db_adapter.commit()

		# Send 'invite' email and delete new User object if send fails
		if user_manager.send_registered_email:
			try:
				# Send 'invite' email
				_send_registered_email(user, user_email)
			except Exception as e:
				# delete new User object if send  fails
				db_adapter.delete_object(user)
				db_adapter.commit()
				raise e

		# Send user_registered signal
		signals.user_registered.send(current_app._get_current_object(), user=user)

		# Redirect if USER_ENABLE_CONFIRM_EMAIL is set
		if user_manager.enable_confirm_email:
			next = request.args.get('next', _endpoint_url(user_manager.after_register_endpoint))
			return redirect(next)

		# Auto-login after register or redirect to login page
		next = request.args.get('next', _endpoint_url(user_manager.after_confirm_endpoint))
		if user_manager.auto_login_after_register:
			return _do_login_user(user, reg_next)                     # auto-login
		else:
			return redirect(url_for('user.login')+'?next='+reg_next)  # redirect to login page

	# Process GET or invalid POST
	return render_template(user_manager.register_template,
			form=register_form,
			login_form=login_form,
			register_form=register_form)

@app.route('/_invite_sent')
def invite_sent():
	return render_template('invite_sent.html')

@app.route("/_admin_remove_filters")
def get_all_food_resource_data():
	food_resource_types = FoodResourceType.query \
		.order_by(FoodResourceType.name_plural).all()

	return jsonify(days_of_week=days_of_week, 
		food_resource_types=[i.serialize_food_resource_type() for i in \
			food_resource_types])

@app.route('/_admin_apply_filters')
def get_filtered_food_resource_data():
	# Collect boolean paramaters passed via JSON.
	has_zip_code_filter = request.args.get('has_zip_code_filter', 0, type=int)
	zip_code = request.args.get('zip_code', 0, type=int)
	has_families_and_children_filter = request.args.get(
		'has_families_and_children_filter', 0, type=int) 
	has_seniors_filter = request.args.get('has_seniors_filter', 0, type=int) 
	has_wheelchair_accessible_filter = request.args.get(
		'has_wheelchair_accessible_filter', 0, type=int) 
	has_accepts_snap_filter = request.args.get(
		'has_accepts_snap_filter', 0, type=int) 

	# Create empty arrays to hold food resources.
	all_resources = []
	food_resource_types = FoodResourceType.query \
		.order_by(FoodResourceType.name_plural).all()

	# Zip code is one of the filters.
	if has_zip_code_filter:

		# Iterate through all food resource types.
		for i, food_resource_type in enumerate(food_resource_types):

			# Filter for each kind of food resource with a specific zip code.
			all_resources.append([])
			get_food_resources_by_location_type_and_zip_code(
				all_resources[i], # List to populate.
				food_resource_type, # Location type by which to filter.
				zip_code # Zip code by which to filter.
			)

			print all_resources[i]

	# Zip code is not one of the filters. 
	else: 

		# Iterate through all food resource types.
		for i, food_resource_type in enumerate(food_resource_types):

			# Filter for each kind of food resource without a specific zip code.
			all_resources[i] = []
			get_food_resources_by_location_type(
				all_resources[i], # List to populate.
				food_resource_type # Location type by which to filter.
			)

	# Filter each list by other boolean criteria.
	for list_to_filter in all_resources:
		filter_food_resources(list_to_filter, has_families_and_children_filter, 
			has_seniors_filter, has_wheelchair_accessible_filter,
			has_accepts_snap_filter)

	json = []
	for i, list in enumerate(all_resources):
		json.append([])
		for food_resource in list:
			json[i].append(food_resource.serialize_food_resource())

	return jsonify(days_of_week=days_of_week, food_resources=json)

@app.route('/map')
def map():
	return render_template('newmaps.html')

@app.route('/_map')
def address_food_resources():
	zip_code = request.args.get('zip_code', 0, type=int)
	food_resources = db.session.query(FoodResource) \
		.join(FoodResource.address) \
		.filter(Address.zip_code==zip_code) \
		.order_by(FoodResource.name).all()
	return jsonify(addresses=[i.serialize_food_resource() for i in food_resources])

@app.route('/_edit', methods=['GET', 'POST'])
def save_page():
	data = request.form.get('edit_data')
	name = request.form.get('page_name')
	if(data):
		page = HTML.query.filter_by(page = name).first()
		page.value = data
		db.session.commit()
	return 'Added' + data + 'to database.'

@app.route('/_remove_food_resource_type')
def remove_food_resource_type():
	id = request.args.get("id", type=int)
	food_resource_type = FoodResourceType.query.filter_by(id=id).first()

	# Remove the food resource type from the database.
	db.session.delete(food_resource_type)
	db.session.commit()
	return jsonify(success="success")

@app.route('/_remove')
def remove():
	id = request.args.get("id", type=int)
	food_resource = FoodResource.query.filter_by(id=id).first()

	# Determine whether the food resource being removed is approved or pending.
	# Needed for front-end update after food resource is removed.
	is_approved = False
	if (food_resource.is_approved):
		is_approved = True

	# If the food resource has a contact and its contact has submitted no other 
	# food resources to the database, remove him/her from the database.
	contact = food_resource.food_resource_contact
	if contact and len(contact.food_resource) <= 1:
		db.session.delete(contact)

	# Remove the food resource from the database.
	db.session.delete(food_resource)
	db.session.commit()
	return jsonify(is_approved=is_approved)

@app.route('/_approve')
def approve():
	id = request.args.get("id", type=int)
	food_resource = FoodResource.query.filter_by(id=id).first()
	contact = food_resource.food_resource_contact

	if len(contact.food_resource) <= 1:
		db.session.delete(contact)
	else:
		contact.food_resource.remove(food_resource)

	food_resource.is_approved = True
	db.session.commit()
	return jsonify(message="success")

@app.route('/about')
def about():
	return render_template('about.html', 
		html_string = HTML.query.filter_by(page = 'about-page').first())

@app.route('/faq')
def faq():
	return render_template('faq.html', 
		html_string = HTML.query.filter_by(page = 'faq-page').first())

@app.route('/contact')
def contact():
	return render_template('contact.html', 
		html_string = HTML.query.filter_by(page = 'contact-page').first())

@app.route('/resources/wic')
def wic():
	return render_template('wic_info.html', 
		html_string = HTML.query.filter_by(page = 'wic-info-page').first())

@app.route('/resources/snap')
def snap():
	return render_template('snap_info.html', 
		html_string = HTML.query.filter_by(page = 'snap-info-page').first())

@app.route('/resources/summer-meals')
def summer_meals():
	return render_template('summer_meals.html', 
		html_string = HTML.query.filter_by(page = 'summer-info-page').first())

@app.route('/resources/seniors')
def seniors():
	return render_template('seniors_info.html', 
		html_string = HTML.query.filter_by(page = 'seniors-info-page').first())

@app.route('/admin/food-resource-types')
@login_required
def view_food_resource_types():
	food_resource_types = FoodResourceType.query \
		.order_by(FoodResourceType.name_singular).all()
	return render_template('food_resource_types.html', 
		food_resource_types=food_resource_types)

@app.route('/admin/new-food-resource-type', methods=['GET', 'POST'])
@app.route('/admin/edit-food-resource-type/<id>', methods=['GET', 'POST'])
@login_required
def new_food_resource_type(id=None):
	form = AddNewFoodResourceTypeForm(request.form)
	form.id.data = None

	# Create a new food resource. 
	if id is None:
		title = "Add New Food Resource Type"
	# Edit an existing food resource.
	else:
		title = "Edit Food Resource Type"
		food_resource_type = FoodResourceType.query.filter_by(id=id).first()
		if food_resource_type is not None:
			form.id.data = food_resource_type.id

	# GET request.
	if request.method == 'GET' and id is not None:

		# Retrieve existing food resource type. 
		food_resource_type = FoodResourceType.query.filter_by(id=id).first()
		if food_resource_type is None:
			return render_template('404.html')

		# Pre-populate form fields with data from database.
		form.name_singular.data = food_resource_type.name_singular
		form.name_plural.data = food_resource_type.name_plural
		form.hex_color.data = food_resource_type.hex_color

	if request.method == 'POST' and form.validate():
		# If editing an existing food resource type, delete its current record
		# from the database. 
		if id is not None:
			food_resource_type = FoodResourceType.query.filter_by(id=id).first()
			if food_resource_type:
				form.id.data = food_resource_type.id
				db.session.delete(food_resource_type)
				db.session.commit()

		# Create new food resource type.
		food_resource_type = FoodResourceType(
			name_singular = form.name_singular.data, 
			name_plural = form.name_plural.data, 
			hex_color = form.hex_color.data, 
			pin_image_name = None
		)
		db.session.add(food_resource_type)
		db.session.commit()

		return redirect(url_for('view_food_resource_types'))

	return render_template('add_resource_type.html', 
		form=form, title=title)
