import csv
from flask import Flask,render_template,request,redirect,url_for
app=Flask(__name__)

# Home page
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
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
