import os
import matplotlib
matplotlib.use('Agg')  # Use Agg backend (non-GUI) for Matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, render_template, request, redirect, url_for, session, Response, send_from_directory, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import csv
from io import StringIO
from datetime import datetime, time
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import tensorflow
from tensorflow import keras

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "healthub.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "my_secret_key"

db = SQLAlchemy(app)
static_folder = os.path.join(os.path.dirname(__file__), 'static')

# Create the SQLAlchemy instance if it doesn't exist
if 'db' not in locals():
    db = SQLAlchemy(app)

# Define your predictive model here and load the trained model

# Load your pre-trained model
model = keras.models.load_model('your_model_path')  # Update with your model path
scaler = StandardScaler()  # Use the same scaler as in training

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


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = USERS.query.filter_by(email=email, password=password).first()
        if user:
            session['email'] = email
            return redirect(url_for('dashboard'))

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
            date_str = request.form.get('date')
            time_str = request.form.get('time')

            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            time = datetime.strptime(time_str, '%H:%M').time()

            health_data = HealthData(
                user_id=user.id,
                heart_rate=heart_rate,
                blood_pressure=blood_pressure,
                stress_level=stress_level,
                weight=weight,
                date=date,
                time=time,
            )
            db.session.add(health_data)
            db.session.commit()

        health_data = HealthData.query.filter_by(user_id=user.id).all()

        health_status_list = []
        for data in health_data:
            new_data = np.array([[data.heart_rate, data.blood_pressure, data.stress_level, data.weight]])
            new_data = scaler.transform(new_data)
            predicted_risk = model.predict(new_data)
            health_status = "Healthy" if predicted_risk <= 0.5 else "At Risk"
            health_status_list.append((predicted_risk, health_status))

        zipped_data = zip(health_data, health_status_list)

        plot_filename = create_health_data_plot(health_data)

        return render_template('dashboard.html', user=user, zipped_data=zipped_data, plot_filename=plot_filename)

    return redirect(url_for('login'))


@app.route('/predict', methods=['POST'])
def predict_health_risk():
    if request.method == 'POST':
        try:
            data = request.get_json()  # Get user's data in JSON format

            # Check if all required keys are present in the JSON data
            required_keys = ['heart_rate', 'blood_pressure', 'stress_level', 'weight']
            if not all(key in data for key in required_keys):
                return jsonify({"error": "Missing required data"}), 400

            # Preprocess the data
            new_heart_rate = data.get('heart_rate')
            new_blood_pressure = data.get('blood_pressure')
            new_stress_level = data.get('stress_level')
            new_weight = data.get('weight')

            # Extract numerical values from 'Blood Pressure'
            new_blood_pressure_values = [float(val) for val in new_blood_pressure.split('/')]

            # Create an array with the new data
            new_data = np.array([[new_blood_pressure_values[0], new_stress_level, new_weight]])

            # Standardize the new data (use the same scaler as in training)
            scaler = StandardScaler()  # Make sure to save and load the same scaler during training
            new_data = scaler.transform(new_data)

            # Make predictions using the loaded model
            predicted_risk = predictive_model.predict(new_data)

            # Determine the health status based on the prediction
            health_status = "Healthy" if predicted_risk <= 0.5 else "At Risk"

            # Return the result as JSON
            result = {
                "predicted_risk": float(predicted_risk[0][0]),
                "health_status": health_status
            }

            return jsonify(result)

        except Exception as e:
            return jsonify({"error": str(e)}), 400


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


@app.route('/static/<filename>')
def serve_static(filename):
    response = make_response(send_from_directory('static', filename))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


def create_health_data_plot(health_data):
    # Extract relevant data for the plots
    dates = [data.date for data in health_data]
    heart_rates = [data.heart_rate for data in health_data]
    weights = [data.weight for data in health_data]
    blood_pressures = [data.blood_pressure for data in health_data]

    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Plot Heart Rate Over Time
    axes[0, 0].set_title("Heart Rate Over Time")
    axes[0, 0].set_xlabel("Date")
    axes[0, 0].set_ylabel("Heart Rate (bpm)")
    axes[0, 0].tick_params(axis='x', rotation=90)
    sns.lineplot(x=dates, y=heart_rates, ax=axes[0, 0])

    # Plot Weight Over Time
    axes[0, 1].set_title("Weight Over Time")
    axes[0, 1].set_xlabel("Date")
    axes[0, 1].set_ylabel("Weight (kg)")
    axes[0, 1].tick_params(axis='x', rotation=90)
    sns.lineplot(x=dates, y=weights, ax=axes[0, 1])

    # Plot Blood Pressure Over Time
    axes[1, 0].set_title("Blood Pressure Over Time")
    axes[1, 0].set_xlabel("Date")
    axes[1, 0].set_ylabel("Blood Pressure")
    axes[1, 0].tick_params(axis='x', rotation=90)
    sns.lineplot(x=dates, y=blood_pressures, ax=axes[1, 0])

    # Plot Relationship Between Heart Rate and Weight
    axes[1, 1].set_title("Relationship: Heart Rate vs. Weight")
    axes[1, 1].set_xlabel("Heart Rate (bpm)")
    axes[1, 1].set_ylabel("Weight (kg)")
    axes[1, 0].tick_params(axis='x', rotation=90)
    sns.scatterplot(x=heart_rates, y=weights, ax=axes[1, 1])

    plt.tight_layout()

    # Save the plot to a temporary file
    # plot_filename = "static/temp_plot.png"
    plot_filename = os.path.join(static_folder, 'temp_plot.png')
    plt.savefig(plot_filename)

    return plot_filename


def calculate_health_score(health_data):
    # You can define your own algorithm to calculate the health score here
    # For example, you can assign scores to different health parameters and calculate a total score
    # A positive score indicates a healthier status, while a negative score indicates an unhealthy status
    health_score = 0
    for data in health_data:
        # Add your scoring logic here, e.g., increase health_score for lower heart rate, etc.
        # Adjust the scoring logic based on your specific requirements
        pass
    return health_score


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
