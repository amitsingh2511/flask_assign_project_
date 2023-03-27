from flask import Flask, request, jsonify, make_response
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy
import uuid # for public id

import jwt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.debug = True

app.config['SECRET_KEY'] = 'YW1pdHNpbmdo'

# adding configuration for using a sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:8969037429@localhost:5432/ta_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# Creating an SQLAlchemy instance
db = SQLAlchemy(app)

# app.app_context().push()


# Models
class Profile(db.Model):
	# Id : Field which stores unique id for every row in
	# database table.
    __tablename__ = "TA"

    id = db.Column(db.Integer, primary_key=True)
    native_english_speaker = db.Column(db.String(250), nullable=False)
    course_instructor = db.Column(db.String(250))
    course = db.Column(db.String(250))
    semester = db.Column(db.Integer)
    class_size = db.Column(db.Integer)
    performance_score = db.Column(db.Float)

    def __repr__(self):
        return "<Profile %r>" % self.native_english_speaker

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(50), unique = True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique = True)
    password = db.Column(db.String(80))
        

if __name__ == '__main__':
    app.run()



def token_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		token = None
		# jwt is passed in the request header
		if 'x-access-token' in request.headers:
			token = request.headers['x-access-token']
			print("token=====",token)
		# return 401 if token is not passed
            
		if not token:
			return jsonify({'message' : 'Token is missing !!'}), 401
        
		try:
			# decoding the payload to fetch the stored details
			data = jwt.decode(token, app.config['SECRET_KEY'])
			print("data==========",data)
			print("public_id==========",data['public_id'])
			current_user = User.query\
				.filter_by(public_id = data['public_id'])\
				.first()
		except:
			return jsonify({
				'message' : 'Token is invalid !!'
			}), 401
		# returns the current logged in users context to the routes
		return f(current_user, *args, **kwargs)

	return decorated

@app.route('/items/<id>', methods=['GET'])
def get_item(id):
  item = Profile.query.get(id)
  if item is None:
     return "data does not exsit."
  del item.__dict__['_sa_instance_state']
  return jsonify(item.__dict__)

@app.route('/items', methods=['GET'])
@token_required
def get_items(current_user):
  items = []
  for item in db.session.query(Profile).all():
    del item.__dict__['_sa_instance_state']
    items.append(item.__dict__)
  return jsonify(items)

@app.route('/items', methods=['POST'])
@token_required
def create_item(current_user):
  body = request.get_json()
  native_english_speaker = body['native_english_speaker']
  course_instructor = body['course_instructor']
  course = body['course']
  semester = body['semester']
  class_size = body['class_size']
  performance_score = body['performance_score']
  print("body=====",body)
  data =Profile(
            native_english_speaker=native_english_speaker,
            course_instructor=course_instructor,
            course=course,
            semester=semester,
            class_size=class_size,
            performance_score=performance_score
        )
  db.session.add(data)
  db.session.commit()
  return "item created"

@app.route('/items/<id>', methods=['PUT'])
@token_required
def update_item(current_user,id):
  body = request.get_json()
  db.session.query(Profile).filter_by(id=id).update(
    dict(title=body['title'], content=body['content']))
  db.session.commit()
  return "item updated"

@app.route('/items/<id>', methods=['DELETE'])
@token_required
def delete_item(current_user,id):
#   id: int
  db.session.query(Profile).filter_by(id=id).delete()
  db.session.commit()
  return "item deleted"


# User Database Route
# this route sends back list of users
@app.route('/user', methods =['GET'])
@token_required
def get_all_users(current_user):
	# querying the database
	# for all the entries in it
	users = User.query.all()
	# converting the query objects
	# to list of jsons
	output = []
	for user in users:
		# appending the user data json
		# to the response list
		output.append({
			'public_id': user.public_id,
			'name' : user.name,
			'email' : user.email
		})

	return jsonify({'users': output})

# route for logging user in
@app.route('/login', methods =['POST'])
def login():
	# creates dictionary of form data
	auth = request.form

	if not auth or not auth.get('email') or not auth.get('password'):
		# returns 401 if any email or / and password is missing
		return make_response(
			'Could not verify',
			401,
			{'WWW-Authenticate' : 'Basic realm ="Login required !!"'}
		)

	user = User.query\
		.filter_by(email = auth.get('email'))\
		.first()

	if not user:
		# returns 401 if user does not exist
		return make_response(
			'Could not verify',
			401,
			{'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'}
		)
    	
	if (user.password, auth.get('password')):
		# generates the JWT Token
		token = jwt.encode({
			'public_id': user.public_id,
			'exp' : datetime.utcnow() + timedelta(minutes = 30)
		}, app.config['SECRET_KEY'])
		print('token====',token)
		return make_response(jsonify({'token' : token.decode('UTF-8')}), 201)
	# returns 403 if password is wrong
	return make_response(
		'Could not verify',
		403,
		{'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'}
	)

# signup route
@app.route('/signup', methods =['POST'])
def signup():
	# creates a dictionary of the form data
	data = request.form

	# gets name, email and password
	name, email = data.get('name'), data.get('email')
	password = data.get('password')

	# checking for existing user
	user = User.query\
		.filter_by(email = email)\
		.first()
	if not user:
		# database ORM object
		user = User(
			public_id = str(uuid.uuid4()),
			name = name,
			email = email,
			password = password
		)
		# insert user
		db.session.add(user)
		db.session.commit()

		return make_response('Successfully registered.', 201)
	else:
		# returns 202 if user already exists
		return make_response('User already exists. Please Log in.', 202)


if __name__ == "__main__":
	# setting debug to True enables hot reload
	# and also provides a debugger shell
	# if you hit an error while running the server
	app.run(debug = True)