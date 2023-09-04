import os
import csv
from flask import Flask,render_template,request,redirect,url_for
app=Flask(__name__)

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Check if the CSV file exists
if not os.path.isfile('users.csv'):
    with open('users.csv', mode='w', newline='') as csv_file:
        fieldnames = ['Name', 'Phone', 'Email', 'Password']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with open('users.csv', mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                if row['Email'] == email and row['Password'] == password:
                    return "Login successful!"
    
    return "Invalid email or password. <a href='/'>Go back to Home</a>"

# ...


@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        print("POST request received")
    else:
        print("GET request received")
    # Rest of your registration code here

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']

        # Write the user data to the CSV file
        with open('users.csv', mode='a', newline='') as csv_file:
            fieldnames = ['Name', 'Phone', 'Email', 'Password']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Write the header if the file is empty
            if csv_file.tell() == 0:
                writer.writeheader()

            writer.writerow({'Name': name, 'Phone': phone, 'Email': email, 'Password': password})

        return redirect(url_for('registration_success'))

    return render_template('register.html')

# Route to display a registration success page

@app.route('/registration-success')
def registration_success():
    return "Registration successful!"

if __name__ =="__main__":
    app.run(debug=True)
