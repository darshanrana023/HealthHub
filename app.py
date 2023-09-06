import os
from flask import Flask, render_template, request, redirect, url_for, session, Response
# from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import csv
from io import StringIO
from datetime import datetime
# from sqlalchemy.sql import func
# import secrets


#initialize flask app
app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

#connection with the databse of xampp mysql
app.config['SQLALCHEMY_DATABASE_URI'] ='mysql://darshan029:D%40rsh%40n029@localhost:3306/healthub'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "my_secret_key"
db = SQLAlchemy(app)

#users database
class USERS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))

    def __repr__(self):
        return f'<Email {self.email}>'

#health data of users
class HealthData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    heart_rate = db.Column(db.Integer, nullable=False)
    blood_pressure = db.Column(db.String(255), nullable=False)
    stress_level = db.Column(db.String(255), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'<HealthData {self.id}>'

# Routes
@app.route('/')
def home():
    return render_template('home.html')

# Route for user registration
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        new_user = USERS(name=name, phone=phone, email=email, password=password)
        
        try:
            with app.app_context():
                db.session.add(new_user)
                db.session.commit()
            # flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('home'))
        except IntegrityError:
            db.session.rollback()
            # flash('Email already registered. Please use a different email.', 'danger')

    return render_template('register.html')


@app.route('/login', methods=['POST','GET'])
def login():
    if request.method== 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = USERS.query.filter_by(email=email, password=password).first()
        if user:
            session['email'] = email
            return render_template('dashboard.html', user=user)  # Render the dashboard template
        else:
        # flash('Invalid email or password. Please try again.', 'danger')  # Show an error message
            return redirect(url_for('login.html'))  # Redirect to the login page

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    email = session.get('email')
    if email:
        user = USERS.query.filter_by(email=email).first()
        if request.method == 'POST':
            # Collect health data from the form
            heart_rate = request.form.get('heartRate')
            blood_pressure = request.form.get('bloodPressure')
            stress_level = request.form.get('stressLevel')
            weight = request.form.get('weight')
            date = request.form.get('date')
            time = request.form.get('time')

            # Create a new HealthData entry and associate it with the user
            health_data = HealthData(
                user_id=user.id,
                heart_rate=heart_rate,
                blood_pressure=blood_pressure,
                stress_level=stress_level,
                weight=weight,
                date=date,
                time=time
            )
            db.session.add(health_data)
            db.session.commit()
    
        # Retrieve the user's health data
        health_data = HealthData.query.filter_by(user_id=user.id).all()
        return render_template('dashboard.html', user=user, health_data=health_data)

    return redirect(url_for('login'))
 
@app.route('/download_csv', methods=['POST'])
def download_csv():
    email = session.get('email')
    if email:
        user = USERS.query.filter_by(email=email).first()
        if user:
            health_data = HealthData.query.filter_by(user_id=user.id).all()

            # Create a CSV string from the health data
            csv_data = StringIO()
            csv_writer = csv.writer(csv_data)
            csv_writer.writerow(['Date', 'Heart Rate', 'Blood Pressure', 'Stress Level', 'Weight', 'Time'])
            for data in health_data:
                csv_writer.writerow([data.date, data.heart_rate, data.blood_pressure, data.stress_level, data.weight, data.time])

            # Create a Flask response with the CSV data
            response = Response(
                csv_data.getvalue(),
                content_type='text/csv',
            )

            # Set the filename based on the user's name and date
            filename = f"{user.name}_{datetime.today().strftime('%Y-%m-%d')}_health_data.csv"
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
            return response

    return redirect(url_for('login'))

# Route for user logout
@app.route('/logout')
def logout():
    session.pop('email', None)
    return render_template('login.html')

if __name__ == '__main__':
    # # Create the database tables
    with app.app_context():
     db.create_all()   
    app.run(debug=True)
 