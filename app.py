import os
from flask import Flask, render_template, request, redirect, url_for, session
# from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

# from sqlalchemy.sql import func
# import secrets

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
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
# Define a route for the dashboard
# @app.route('/dashboard', methods=['GET', 'POST'])
# def dashboard():
#     if 'email' in session:
#         user = User.query.filter_by(email=session['email']).first()

#         if request.method == 'POST':
#             data_file = request.files['dataFile']
#             if data_file:
#                 filename = secure_filename(data_file.filename)
#                 data_file.save(filename)

#                 # Assuming the CSV file has columns: 'Date', 'Heart Rate', 'Sleep Patterns', 'Exercise Logs'
#                 health_data_df = pd.read_csv(filename)
#                 health_data = health_data_df.to_dict(orient='records')

#                 # You can save this data to the user's specific file or database
#                 # For simplicity, we're just storing it in memory in this example
#                 user.health_data = health_data
#                 db.session.commit()

#         else:
#             health_data = user.health_data or []

#         return render_template('dashboard.html', user=user, health_data=health_data)

#     return redirect(url_for('login')) 

# Route for user logout
@app.route('/logout')
def logout():
    session.pop('email', None)
    return render_template('home.html')

# Route to display a registration success page
# @app.route('/registration-success')
# def registration_success():
#     return "Registration successful!"

if __name__ == '__main__':
    # # Create the database tables
    with app.app_context():
     db.create_all()   
    app.run(debug=True)
 