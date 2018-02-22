from flask import Flask, render_template, request, redirect, session, flash
from passlib.hash import pbkdf2_sha256
from forms import ContactForm
from flask_mail import Mail, Message
from db import connection

import flask_login
import time
from datetime import datetime
import MySQLdb
import configparser
import os
import atexit

app = Flask(__name__)
app.secret_key = os.urandom(12)
version = '0.4.3'

last_update_dict = {"AA:BB:CC:DD:EE:FF": 0} #used to store the last update recieved from a device

db, cur = connection()
cur.execute("SELECT MAC FROM Devices")
for row in cur.fetchall():
    last_update_dict[row[0]] = 0

valid_keys = ["temperature", "co2", "pressure", "humidity", "altitude", "sound", "MAC", "voc", "light", "button", "motion"]

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == "POST":
		if request.form['MAC'] in last_update_dict:
			if (time.time() - last_update_dict[request.form['MAC']]) < 300:
				return "Too Many Requests."
			else:
				cur = db.cursor()
				last_update_dict[request.form['MAC']] = time.time()
				insert_string_variables = ["deviceID", "timeRecieved"]
				cur.execute("SELECT deviceID FROM Devices WHERE MAC='" + request.form['MAC'] + "'")
				insert_string_values = [str(cur.fetchall()[0][0]), str(last_update_dict[request.form['MAC']])]
				for key in request.form:
					if str(key) in valid_keys:
						insert_string_variables.append(str(key))
						if str(key) == "MAC":
							insert_string_values.append('"' + str(request.form[key]) + '"')
						else:
							insert_string_values.append(str(request.form[key]))

					else:
						return "Key Error"
        print("POST FROM -- " + request.form['MAC'])
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
    try: 
        cur.execute("SELECT deviceID,name,descr,lat,lon FROM  Devices")
        for row in cur.fetchall():
            location_info.append({
                'id':row[0],
                'name':row[1], 
                'varname':row[1].replace(' ', '_'), 
                'coords':{'lat':row[3], 'lon':row[4]}, 
                'desc':row[2]
	        })
    except:
        print("Error pulling data from mariadb")

    return render_template('map.html', location_info=location_info)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"] or "null"
        password = request.form["password"] or "null"

        try:
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

        except:
            print("Error accessing database.")
            error = "Our server is experiencing issues processing your request."
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
				errors = False
				names = []
				macs = []
				coords = []
				cur.execute("SELECT name,MAC,lat,lon FROM Devices")
				for row in cur.fetchall():
				       names.append(str(row[0])) 
				       macs.append(str(row[1]))
				       coords.append(str(row[2]) + "," + str(row[3]))
				if(request.form['name'] in names):
					errors = True
					flash("Name already in use")
				if(request.form['MAC'] in macs):
					errors = True
					flash("MAC already in use")
				mod_coords = request.form['lat'].strip("0") + "," + request.form['lon'].strip("0")
				if(mod_coords in coords):
					errors = True
					flash("Device already at that location")
				if(errors):
					form_data = {}
					form_data['name'] = request.form['name']
					form_data['descr'] = request.form['descr']
					form_data['lat'] = request.form['lat']
					form_data['lon'] = request.form['lon']
					form_data['MAC'] = request.form['MAC']
					return render_template("display_add_device.html", form_data=form_data)
				else:
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
					cur.execute(insert_string)
					db.commit()
					last_update_dict[request.form['MAC']] = 0
					flash("Device Succesffuly Added")
                                        form_data = {}
					return render_template("display_add_device.html", form_data=form_data)
			elif request.method == "GET":
				form_data = {}
				return render_template('display_add_device.html',form_data=form_data)
		else:
			return redirect('/login')
	else:
		return redirect('/login')

@app.route('/device/<device_to_display>')
def device(device_to_display):
    device_name = "error"
    device_data = []
    try:
        int(device_to_display) #ensure that the device ID is an integer
    except:
        flash("Invalid device ID")
        return redirect('/map') 
    cur.execute("SELECT name FROM Devices WHERE deviceID=" + device_to_display + " LIMIT 1")
    for row in cur.fetchall():
        device_name = row[0]
    if(device_name == "error"):
        flash("Invalid device ID")
        return redirect('/map')
    cur.execute("SELECT * FROM Data WHERE deviceID=" + device_to_display + " ORDER BY timeRecieved desc")
    for row in cur.fetchall():
        device_data.append({
            'timeRecieved':datetime.fromtimestamp(int(row[1])).strftime("%d %b %Y - %H:%M:%S"),
            'light':row[2],
            'motion':row[3],
            'pressure':row[4],
            'temperature':row[5],
            'humidity':row[6],
            'co2':row[7],
            'button':row[8],
            'altitude':row[9],
            'voc':row[10],
            'sound':row[11]})
    return render_template('display_device.html', device=device_name, data=device_data)

@app.route('/manage')
def manage():
    if session.get('authenticated'):
        if session['authenticated']:
            devices = []
            cur.execute("SELECT deviceID, name FROM Devices")
            for row in cur.fetchall():
                devices.append({'deviceID':row[0], 'varname':row[1].replace(' ', '_'), 'name':row[1]})
            return render_template('manage.html', devices=devices)
        else:
            return redirect('/login')
    else:
        return redirect('/login')

@app.route('/manage_device/<device_to_manage>', methods=['GET', 'POST'])
def manage_device(device_to_manage):
    if session.get('authenticated'):
        if session['authenticated']:
            if request.method == "GET":
                device_info = {}
                cur.execute("SELECT * FROM Devices WHERE deviceID='" + device_to_manage + "' LIMIT 1")
                for row in cur.fetchall():
                    device_info = {
                           'deviceID':row[0],
                           'deviceType':row[1],
                           'name':row[2],
                           'descr':row[3],
                           'coords':{'lat':row[4], 'lon':row[5]},
                           'MAC':row[6]}
                return render_template('manage_device.html', device_info=device_info)
            if request.method == "POST":
                update_string = "UPDATE Devices SET "
                update_string += "name=\"" + str(request.form['name']) + "\","
                update_string += "descr=\"" + str(request.form['descr']) + "\","
                update_string += "lat=" + str(request.form['lat']) + ","
                update_string += "lon=" + str(request.form['lon']) + ","
                update_string += "MAC=\"" + str(request.form['MAC']) + "\""
                update_string += " WHERE deviceID=" + device_to_manage
                cur.execute(update_string)
                db.commit()
                flash("Device Successfully Updated")
                return redirect('/manage')
        else:
            return redirect('/login')
    else:
        return redirect('/login')

@app.route('/contact', methods=['POST'])
def contact():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/iot')
def iot():
    return render_template('iot.html')

@app.route('/backend')
def backend():
    return render_template('backend.html')

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def errorpage(e):
        return render_template('error.html')

def cleanup():
    try:
        cur.close()
    except Exception:
        pass

atexit.register(cleanup)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
