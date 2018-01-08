from flask import Flask, render_template, request, redirect, session, flash
from passlib.hash import pbkdf2_sha256
from forms import ContactForm
from flask_mail import Mail, Message

import flask_login
import time
import MySQLdb
import configparser
import os

app = Flask(__name__)
app.secret_key = os.urandom(12)
version = '0.4.1'

dbcreds = configparser.ConfigParser()
dbcreds.read('db.cfg')


db = MySQLdb.connect(host=dbcreds.get('database', 'host'),
                     user=dbcreds.get('database', 'user'),
                     passwd=dbcreds.get('database', 'passwd'),
                     db=dbcreds.get('database', 'db'))

mail = Mail()
app.config["MAIL_SERVER"] = dbcreds.get('mail', 'server')
app.config["MAIL_PORT"] = dbcreds.get('mail', 'port')
app.config["MAIL_USE_SSL"] = dbcreds.get('mail', 'ssl')
app.config["MAIL_USERNAME"] = dbcreds.get('mail', 'username')
app.config["MAIL_PASSWORD"] = dbcreds.get('mail', 'password')

mail.init_app(app)


last_update_dict = {"5C:CF:7F:AE:D9:65": 0, "AA:BB:CC:DD:EE:FF": 0} #used to store the last update recieved from a device
valid_keys = ["temperature", "co2", "pressure", "humidity", "altitude", "sound", "MAC", "voc", "light", "button", "motion"]

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == "POST":
		if request.form['MAC'] in last_update_dict:
			print(last_update_dict[request.form['MAC']])
			if (time.time() - last_update_dict[request.form['MAC']]) < 300:
				return "Too Many Requests."
			else:
				last_update_dict[request.form['MAC']] = time.time()
				insert_string_variables = ["deviceID", "timeRecieved"]
				insert_string_values = ["0", str(last_update_dict[request.form['MAC']])]	##TODO - get dev ID dynamically
				print("--- POST FROM " + str(request.headers.get('User-Agent')) + " ---" + time.strftime("%H:%M:%S"))
				for key in request.form:
					print("  " + str(key) + " - " + str(request.form[key]))
					if str(key) in valid_keys:
						insert_string_variables.append(str(key))
						if str(key) == "MAC":
							insert_string_values.append('"' + str(request.form[key]) + '"')
						else:
							insert_string_values.append(str(request.form[key]))

					else:
						return "Key Error"

				cur = db.cursor()
				print("INSERT INTO Data (" + ",".join(insert_string_variables) + ") VALUES (" + ",".join(insert_string_values) + ")")
				cur.execute("INSERT INTO Data (" + ",".join(insert_string_variables) + ") VALUES (" + ",".join(insert_string_values) + ")")
				db.commit()

				return "Success!"
		else:
			return "Could not verify MAC."
	else:
		session['version'] = version
		return render_template('index.html', form=ContactForm())

@app.route('/map')
def map():
	location_info = []
	cur = db.cursor()
	cur.execute("SELECT deviceID,name,descr,lat,lon FROM  Devices")
	for row in cur.fetchall():
	    location_info.append({
	    	'id':row[0],
	    	'name':row[1], 
	    	'varname':row[1].replace(' ', '_'), 
	    	'coords':{'lat':row[3], 'lon':row[4]}, 
	    	'desc':row[2]
	    })
	return render_template('map.html', location_info=location_info)

@app.route('/device/<device_to_display>')
def device(device_to_display):
	return render_template('display_device.html', device=device_to_display)

@app.route('/login', methods=['GET', 'POST'])
def login():
        if request.method == "POST":

                username = request.form["username"] or "null"
                password = request.form["password"] or "null"

                cur = db.cursor()
                cur.execute("SELECT COUNT(1) FROM Users WHERE email = %s;", [username])
                if cur.fetchone()[0]:
                    cur.execute("SELECT salt FROM Users WHERE email = %s;", [username])
                    salt = cur.fetchall()
                    password = password + salt[0][0]
                    cur.execute("SELECT hash FROM Users WHERE email = %s;", [username])
                    passhash = cur.fetchall()
                    if pbkdf2_sha256.verify(password, passhash[0][0]):
                        session['authenticated'] = True
                        session['username'] = username
                        return redirect('/')
                    else:
                        error = "Incorrect username or password!"
                        return render_template("login.html", error=error)
                else:
                    error = "Incorrect username or password!"
                    return render_template("login.html", error=error)
                        
        elif request.method == "GET":
            return render_template("login.html")

@app.route('/logout')
def logout():
	session['authenticated'] = False
	return redirect('/')

@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
	if session.get('authenticated'):
		if session['authenticated']:
			if request.method == "POST":
				cur = db.cursor()
				deviceID = 0
				cur.execute("SELECT deviceID FROM Devices ORDER BY deviceID desc limit 1")
				for row in cur.fetchall():
					deviceID = int(row[0]) + 1
				insert_string = "INSERT INTO Devices (deviceID, deviceType, name, descr, lat, lon, MAC) VALUES ("
				insert_string += str(deviceID) + ","
				insert_string += "\"" + str(request.form['deviceType']) + "\","
				insert_string += "\"" + str(request.form['name']) + "\","
				insert_string += "\"" + str(request.form['descr']) + "\","
				insert_string += str(request.form['lat']) + ","
				insert_string += str(request.form['lon']) + ","
				insert_string += "\"" + str(request.form['MAC']) + "\""
				insert_string += ")"
				print(insert_string)
				cur.execute(insert_string)
				db.commit()
				flash("Device Succesffuly Added")
				return render_template("display_add_device.html")
			elif request.method == "GET":
				return render_template('display_add_device.html')
		else:
			return redirect('/login')
	else:
		return redirect('/login')

@app.route('/contact', methods=['POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = Message(form.subject.data, sender='contact@eyecu.colorado.edu', recipients=['ryan.m.bohannon@gmail.com'])
        msg.bodt = """
        From: %s &lt;%s&gt;
        %s
        """ % (form.name.data, form.email.data, form.message.data)
        mail.send(msg)

    return render_template('index.html', form=form)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/redhat')
def redhat():
    return render_template('redhat.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
