
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
# from app import db
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy import func

app = Flask(__name__)
CORS(app)

# Configure the PostgreSQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:autoslip@localhost:5432/Hostel'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable track modifications for performance

# Initialize SQLAlchemy
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


class Block(db.Model):
    __tablename__ = 'blocks'
    block_id = db.Column(db.Integer, primary_key=True)
    block_name = db.Column(db.String(50), nullable=False)
    hostel_number = db.Column(db.Integer, nullable=False)

class Parent(db.Model):
    __tablename__ = 'parents'
    parent_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone_number = db.Column(db.String(15), nullable=False)
    relationship = db.Column(db.String(50))

class Student(db.Model):
    __tablename__ = 'students'
    reg_no = db.Column(db.String(20), primary_key=True)
    cnic = db.Column(db.String(15), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    block_id = db.Column(db.Integer, db.ForeignKey('blocks.block_id'), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.parent_id'))
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    emergency_contact = db.Column(db.String(15), nullable=False)
    room = db.Column(db.String(10), nullable=False)
    
class Slip(db.Model):
    __tablename__ = 'slips'
    slip_id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(20), db.ForeignKey('students.reg_no'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text)
    reason = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    room_no = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    comment = db.Column(db.Text)
    warning_comment = db.Column(db.Text)
    warning_reason = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

class Warning(db.Model):
    __tablename__ = 'warnings'
    warning_id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(20), db.ForeignKey('students.reg_no'), nullable=False)
    issued_by = db.Column(db.String(100))
    reason = db.Column(db.Text)
    issued_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

class Admin(db.Model):
    __tablename__ = 'admins'
    email = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    block_id = db.Column(db.Integer, db.ForeignKey('blocks.block_id'))

class SlipHistory(db.Model):
    __tablename__ = 'slip_history'
    history_id = db.Column(db.Integer, primary_key=True)
    slip_id = db.Column(db.Integer, db.ForeignKey('slips.slip_id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text)
    action_date = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

class Profile(db.Model):
    __tablename__ = 'profiles'
    profile_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), db.ForeignKey('admins.email'))
    reg_no = db.Column(db.String(20), db.ForeignKey('students.reg_no'))
    profile_picture = db.Column(db.LargeBinary)
    bio = db.Column(db.Text)
    updated_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

class Notification(db.Model):
    __tablename__ = 'notifications'
    notification_id = db.Column(db.Integer, primary_key=True)
    slip_id = db.Column(db.Integer, db.ForeignKey('slips.slip_id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.parent_id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    sent = db.Column(db.Boolean, default=False)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Check in Admins table
    admin = Admin.query.filter_by(email=email, password=password).first()
    if admin:
        return jsonify({
            'role': 'admin' if admin.role == 'Main Admin' else 'subAdmin',
            'block_id': admin.block_id,
            'name': admin.name
        }), 200
    
    # Check in Students table
    student = Student.query.filter_by(email=email, password=password).first()
    if student:
        return jsonify({
            'role': 'resident',
            'name': student.name,
            'reg_no': student.reg_no,
            'block_id': student.block_id
        }), 200
    
    # Invalid credentials
    return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/')
def home():
    return "Welcome to the Hostel Management System API"
 
@app.route('/api/students', methods=['GET'])
def get_all_students():
    students = Student.query.all()
    return jsonify([student.name for student in students]), 200


@app.route('/api/students', methods=['POST'])
def create_student():
    data = request.get_json()
    new_student = Student(
        reg_no=data['reg_no'],
        name=data['name'],
        cnic=data['cnic'],
        block_id=data['block_id'],
        password=data['password'],
        parent_id=data.get('parent_id', None)
    )
    db.session.add(new_student)
    db.session.commit()
    return jsonify({'message': 'Student created successfully'}), 201


@app.route('/api/students/<reg_no>', methods=['GET'])
def get_student_data(reg_no):
    # print(f"Received reg_no: {reg_no}")  # Debug print
    student = Student.query.filter_by(reg_no=reg_no).first()

    if not student:
        return jsonify({'error': 'Student not found'}), 404
    return jsonify({
        'reg_no': student.reg_no,
        'name': student.name,
        'cnic': student.cnic,
        'block_id': student.block_id,
        'email': student.email,
    }), 200

@app.route('/api/students/update_password', methods=['POST'])
def update_password():
    data = request.json
    reg_no = data.get('reg_no')
    new_password = data.get('new_password')
    student = Student.query.filter_by(reg_no=reg_no).first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    student.password = new_password  # Replace this with hashing logic
    db.session.commit()
    return jsonify({'message': 'Password updated successfully'}), 200

# @app.route('/api/student/<string:reg_no>', methods=['GET'])
# def get_student_data(reg_no):
#     if reg_no == "null" or not reg_no:
#         return jsonify({'error': 'Invalid registration number'}), 400
#     student = Student.query.filter_by(reg_no=reg_no).first()
#     if not student:
#         return jsonify({'error': 'Student not found'}), 404
#     return jsonify({
#         'reg_no': student.reg_no,
#         'name': student.name,
#         'cnic': student.cnic,
#         'block_id': student.block_id,
#         'email': student.email,
#     }), 200

# @app.route('/api/student/update_password', methods=['POST'])
# def update_password():
#     data = request.get_json()
#     reg_no = data.get('reg_no')
#     current_password = data.get('current_password')
#     new_password = data.get('new_password')

#     student = Student.query.filter_by(reg_no=reg_no).first()
#     if not student:
#         return jsonify({'error': 'Student not found'}), 404

#     if not bcrypt.check_password_hash(student.password, current_password):
#         return jsonify({'error': 'Current password is incorrect'}), 401

#     student.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
#     db.session.commit()
#     return jsonify({'message': 'Password updated successfully'}), 200

# @app.route('/api/student/update_password', methods=['PUT'])
# def update_password():
#     data = request.get_json()
#     reg_no = data.get('reg_no')
#     current_password = data.get('current_password')
#     new_password = data.get('new_password')

#     student = Student.query.filter_by(reg_no=reg_no).first()
#     if not student:
#         return jsonify({'error': 'Student not found'}), 404

#     if student.password != current_password:
#         return jsonify({'error': 'Current password is incorrect'}), 401

#     student.password = new_password
#     db.session.commit()
#     return jsonify({'message': 'Password updated successfully'}), 200
# @app.route('/api/student', methods=['GET'])
# @jwt_required()
# def get_student_profile():
#     current_user = get_jwt_identity()
#     student = Student.query.filter_by(email=current_user).first()
#     if not student:
#         return jsonify({"message": "Student not found"}), 404
#     return jsonify({
#         "reg_no": student.reg_no,
#         "student_name": student.student_name,
#         "cnic": student.cnic,
#         "block_id": student.block_id,
#         "room_number": student.room_number,
#         "contact_number": student.contact_number,
#         "email": student.email,
#         "parent_contact": student.parent_contact,
#         "emergency_contact": student.emergency_contact,
#     })

# @app.route('/api/change-password', methods=['POST'])
# @jwt_required()
# def change_password():
#     current_user = get_jwt_identity()
#     data = request.get_json()
#     current_password = data.get('currentPassword')
#     new_password = data.get('newPassword')

#     student = Student.query.filter_by(email=current_user).first()
#     if not student or not bcrypt.check_password_hash(student.password_hash, current_password):
#         return jsonify({"message": "Current password is incorrect"}), 400

#     student.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
#     db.session.commit()
#     return jsonify({"message": "Password updated successfully"}), 200
   
@app.route('/api/slips', methods=['GET'])
def get_all_slips():
    slips = Slip.query.all()
    return jsonify([{
        'slip_id': slip.slip_id,
        'reg_no': slip.reg_no,
        'status': slip.status
    } for slip in slips]), 200

@app.route('/api/slips', methods=['POST'])
def create_slip():
    data = request.get_json()
    new_slip = Slip(
        reg_no=data['reg_no'],
        type=data['type'],
        address=data.get('address'),
        reason=data.get('reason'),
        date=data['date'],
        time=data['time'],
        room_no=data['room_no']
    )
    db.session.add(new_slip)
    db.session.commit()
    return jsonify({'message': 'Slip created successfully'}), 201

@app.route('/api/warnings/<string:reg_no>', methods=['GET'])
def get_warnings_for_student(reg_no):
    warnings = Warning.query.filter_by(reg_no=reg_no).all()
    return jsonify([{
        'warning_id': warning.warning_id,
        'reason': warning.reason,
        'issued_at': warning.issued_at
    } for warning in warnings]), 200

@app.route('/api/profiles/<string:reg_no>', methods=['GET'])
def get_profile_info(reg_no):
    profile = Profile.query.filter_by(reg_no=reg_no).first()
    if profile:
        return jsonify({
            'bio': profile.bio,
            'profile_picture': profile.profile_picture
        }), 200
    return jsonify({'message': 'Profile not found'}), 404

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    with app.app_context():  # Ensure proper application context
        db.create_all()  # Create all tables in the database
    app.run(debug=True)

# # Define a sample model
# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)

#     def __repr__(self):
#         return f'<User {self.name}>'

# @app.route('/')
# def index():
#     return 'Hello, World! Database connected!'

# if __name__ == '__main__':
#     # Uncomment this line to create tables in the database
#      db.create_all()
#     app.run(debug=True)

