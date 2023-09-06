import os
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] ='mysql://darshan029:D%40rsh%40n029@localhost:3306/healthub'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "my_secret_key"
db = SQLAlchemy(app)

class USERS(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))

    def __repr__(self):
        return f'<Email {self.email}>'

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

@app.route('/')
def home():
    return render_template('home.html')

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
            return redirect(url_for('home'))
        except IntegrityError:
            db.session.rollback()

    return render_template('register.html')

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = USERS.query.filter_by(email=email, password=password).first()
        if user:
            session['email'] = email
            return render_template('dashboard.html', user=user)
        else:
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    email = session.get('email')
    if email:
        user = USERS.query.filter_by(email=email).first()
        if request.method == 'POST':
            heart_rate = request.form.get('heartRate')
            blood_pressure = request.form.get('bloodPressure')
            stress_level = request.form.get('stressLevel')
            weight = request.form.get('weight')
            date = request.form.get('date')
            time = request.form.get('time')

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
    
        health_data = HealthData.query.filter_by(user_id=user.id).all()

        plot_filename = create_health_data_plot(health_data)

        return render_template('dashboard.html', user=user, health_data=health_data, plot_filename=plot_filename)

    return redirect(url_for('login'))

@app.route('/download_csv', methods=['POST'])
def download_csv():
    email = session.get('email')
    if email:
        user = USERS.query.filter_by(email=email).first()
        if user:
            health_data = HealthData.query.filter_by(user_id=user.id).all()

            csv_data = StringIO()
            csv_writer = csv.writer(csv_data)
            csv_writer.writerow(['Date', 'Heart Rate', 'Blood Pressure', 'Stress Level', 'Weight', 'Time'])
            for data in health_data:
                csv_writer.writerow([data.date, data.heart_rate, data.blood_pressure, data.stress_level, data.weight, data.time])

            response = Response(
                csv_data.getvalue(),
                content_type='text/csv',
            )

            filename = f"{user.name}_{datetime.today().strftime('%Y-%m-%d')}_health_data.csv"
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
            return response

    return redirect(url_for('login'))

def create_health_data_plot(health_data):
    dates = [data.date for data in health_data]
    heart_rates = [data.heart_rate for data in health_data]

    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    plt.title("Heart Rate Over Time")
    plt.xlabel("Date")
    plt.ylabel("Heart Rate (bpm)")
    sns.lineplot(x=dates, y=heart_rates, marker='o', label='Heart Rate')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    plot_filename = "static/temp_plot.png"
    plt.savefig(plot_filename)

    return plot_filename

@app.route('/logout')
def logout():
    session.pop('email', None)
    return render_template('login.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
