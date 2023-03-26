from flask import Flask, request, jsonify
from flask.templating import render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.debug = True

# adding configuration for using a sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:8969037429@localhost:5432/ta_db'

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

if __name__ == '__main__':
    app.run()


@app.route('/items/<id>', methods=['GET'])
def get_item(id):
  item = Profile.query.get(id)
  if item is None:
     return "data does not exsit."
  del item.__dict__['_sa_instance_state']
  return jsonify(item.__dict__)

@app.route('/items', methods=['GET'])
def get_items():
  items = []
  for item in db.session.query(Profile).all():
    del item.__dict__['_sa_instance_state']
    items.append(item.__dict__)
  return jsonify(items)

@app.route('/items', methods=['POST'])
def create_item():
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
def update_item(id):
  body = request.get_json()
  db.session.query(Profile).filter_by(id=id).update(
    dict(title=body['title'], content=body['content']))
  db.session.commit()
  return "item updated"

@app.route('/items/<id>', methods=['DELETE'])
def delete_item(id):
  db.session.query(Profile).filter_by(id=id).delete()
  db.session.commit()
  return "item deleted"