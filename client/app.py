from flask import Flask, render_template, request, redirect, session, flash
from flask_socketio import SocketIO
from flask_socketio import emit
from flask_mail import Mail, Message
from conf import dbconnection, motd
import device as dev
import auth as auth

import flask_login
from time import localtime, time, strftime
from datetime import datetime
import MySQLdb
import configparser
import os
import atexit

app = Flask(__name__)
app.secret_key = os.urandom(12)
socketio = SocketIO(app)
version = '0.9.1-3'


last_message = 'Test Device just said HI!'
last_update_dict = {"AA:BB:CC:DD:EE:FF": 0} #used to store the last update recieved from a device
devices = []

# Init db dbconnection
db,cur = dbconnection()
cur.execute("SELECT dev.MAC,dat.timeRecieved FROM Data dat,Devices dev WHERE timeRecieved=(SELECT MAX(timeRecieved) FROM Data dat2 WHERE dat2.deviceID=dev.deviceID)")
for row in cur.fetchall():
	last_update_dict[row[0]] = row[1]
cur.execute("SELECT MAC FROM Devices")
for row in cur.fetchall():
	if not(row[0] in last_update_dict):
		last_update_dict[row[0]] = 0
cur.close()

valid_keys = ["temperature", "co2", "pressure", "humidity", "altitude", "sound", "MAC", "voc", "light", "button", "motion"]


@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == "POST":
		if request.form['MAC'] in last_update_dict:
			if (time() - last_update_dict[request.form['MAC']]) < 300:
				return "Too Many Requests."
			else:
				last_update_dict[request.form['MAC']] = time()
				# call device.py helper function
				msg = dev.add_data(last_update_dict,request)
				devices = dev.device_state(last_update_dict)
				socketio.emit('update', {'msg':msg});
				return "success"

		else:
			print("Could not verify " + request.form['MAC'])
			return "Could not verify MAC."
	else:
		session['version'] = version
		session['motd'] = motd()
		return render_template('index.html')

@app.route('/map')
def map():
	location_info = []
	try: 
		db,cur = dbconnection()
		cur.execute("SELECT deviceID,name,descr,lat,lon FROM Devices ORDER BY name")
		for row in cur.fetchall():
			location_info.append({
			'id':row[0],
			'name':row[1], 
			'varname':row[1].replace(' ', '_'), 
			'coords':{'lat':row[3], 'lon':row[4]}, 
			'desc':row[2]
			})
		cur.close()
	except:
		print("Error pulling data from mariadb")

	return render_template('/device/map.html', location_info=location_info)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == "POST":
		username = request.form["username"] or "null"
		password = request.form["password"] or "null"
		try:
		    if auth.login(username,password):
		        session['authenticated'] = True
		        session['username'] = username
		        msg = ("%s has logged in...something's broken..." % username.upper())
		        socketio.emit('update', {'msg':msg});
		        return redirect('/')
		    else:
		        error = "Incorrect username or password!"
		        return render_template("/admin/login.html", error=error)

		except:
		    print("Error accessing database.")
		    error = "Our server is experiencing issues processing your request."
		    msg = ("Users are having trouble accessing our database...")
		    socketio.emit('update', {'msg':msg});
		    return render_template("/admin/login.html", error=error)
	elif request.method == "GET":
		return render_template("/admin/login.html")

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
				db,cur = dbconnection()
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
					cur.close()
					return render_template("/admin/add_device.html", form_data=form_data)
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
					cur.close()
					last_update_dict[request.form['MAC']] = 0
					msg = ("Device Succesfully Added")
					flash(msg)
					socketio.emit('update', {'msg':msg});
					form_data = {}
					return render_template("/admin/add_device.html", form_data=form_data)
			elif request.method == "GET":
				form_data = {}
				return render_template('/admin/add_device.html',form_data=form_data)
		else:
			return redirect('/login')
	else:
		return redirect('/login')

@app.route('/devices')
def devices():
	devices=dev.device_state(last_update_dict)
	return render_template('/device/devices.html', devices=devices)

@app.route('/devices/<device_to_display>')
def device(device_to_display):
	device_name = "error"
	try:
		int(device_to_display) #ensure that the device ID is an integer
	except:
		flash("Invalid device ID")
		return redirect('/map') 
	data_timeRecieved, data_light, data_motion, data_no_motion, data_pressure, data_temperature, data_humidity, data_co2, data_button_pressed, data_button_not_pressed, data_altitude, data_voc, data_sound = [], [], [], [], [], [], [], [], [], [], [], [], []
	db,cur = dbconnection()
	cur.execute("SELECT name FROM Devices WHERE deviceID=" + device_to_display + " LIMIT 1")
	for row in cur.fetchall():
		device_name = row[0]
	if(device_name == "error"):
		flash("Invalid device ID")
		return redirect('/map')
	cur.execute("SELECT deviceId,timeRecieved,light,motion,pressure,temperature,humidity,co2,button,altitude,voc,sound FROM Data WHERE deviceID=" + device_to_display + " ORDER BY timeRecieved desc LIMIT 2016")
	rows = cur.fetchall()
	if(len(rows)):
		first_data_time = rows[len(rows)-1][1]
		last_data_time = rows[0][1]
	for row in rows:
		data_timeRecieved.append(strftime("%d %b - %H:%M", localtime(int(row[1]))))
		data_light.append(float("%.2f" % row[2]))
		if (row[3]):
			data_motion.append(row[3])
		else:
			data_no_motion.append(row[3])
		data_pressure.append(float("%.2f" % row[4]))
		data_temperature.append(float("%.2f" % (row[5] * (9/5) + 32)))
		data_humidity.append(float("%.2f" % row[6]))
		data_co2.append(float("%.2f" % row[7]))
		if (row[8]):
			data_button_pressed.append(row[8])
		else:
			data_button_not_pressed.append(row[8])
		data_altitude.append(float("%.2f" % row[9]))
		data_voc.append(float("%.2f" % row[10]))
		data_sound.append(float("%.2f" % row[11]))
	if (len(data_timeRecieved) == len(data_light) == len(data_motion) + len(data_no_motion) == len(data_pressure) == len(data_temperature) == len(data_humidity) == len(data_co2) == len(data_button_pressed) + len(data_button_not_pressed) == len(data_altitude) == len(data_voc) == len(data_sound)):
		data = {"timeRecieved": list(reversed(data_timeRecieved)), "light": list(reversed(data_light)), "motion": list(reversed(data_motion)), "no_motion": list(reversed(data_no_motion)), "pressure": list(reversed(data_pressure)), "temperature": list(reversed(data_temperature)), "humidity": list(reversed(data_humidity)), "co2": list(reversed(data_co2)), "button_pressed": list(reversed(data_button_pressed)), "button_not_pressed": list(reversed(data_button_not_pressed)), "altitude": list(reversed(data_altitude)), "voc": list(reversed(data_voc)), "sound": list(reversed(data_sound))} #all data has to be reversed to re-order it chronologically
		if (len(rows)):
			data['expectedSubmissionsPercent'] = len(data_timeRecieved) / ((time() - first_data_time) / 300) * 100
			data['lastDataMins'] = int((time() - last_data_time) / 60)
		cur.close()
		return render_template('/device/single_device.html', device=device_name, data=data)
	else:
		print("Error: Data returned not all the same length")
		flash("Server Error for Device")
		return redirect('/map')

@app.route('/manage')
def manage():
	if session.get('authenticated'):
		if session['authenticated']:
			devices = []
			db,cur = dbconnection()
			cur.execute("SELECT deviceID, name FROM Devices")
			for row in cur.fetchall():
				devices.append({'deviceID':row[0], 'varname':row[1].replace(' ', '_'), 'name':row[1]})
			cur.close()
			return render_template('/admin/manage.html', devices=devices)
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
				db,cur = dbconnection()
				cur.execute("SELECT deviceID,deviceType,name,descr,lat,lon,MAC FROM Devices WHERE deviceID='" + device_to_manage + "' LIMIT 1")
				for row in cur.fetchall():
					device_info = {
					   'deviceID':row[0],
					   'deviceType':row[1],
					   'name':row[2],
					   'descr':row[3],
					   'coords':{'lat':row[4], 'lon':row[5]},
					   'MAC':row[6]}
				cur.close()
				return render_template('/admin/manage_device.html', device_info=device_info)
			elif request.method == "POST":
				db,cur = dbconnection()
				update_string = "UPDATE Devices SET "
				update_string += "name=\"" + str(request.form['name']) + "\","
				update_string += "descr=\"" + str(request.form['descr']) + "\","
				update_string += "lat=" + str(request.form['lat']) + ","
				update_string += "lon=" + str(request.form['lon']) + ","
				update_string += "MAC=\"" + str(request.form['MAC']) + "\""
				update_string += " WHERE deviceID=" + device_to_manage
				cur.execute(update_string)
				db.commit()
				cur.close()
				msg = ("Device Settings Succesfully Updated")
				flash(msg)
				socketio.emit('update', {'msg':msg});
				return redirect('/manage')
			else:
				return errorpage('404')
		else:
			return redirect('/login')
	else:
		return redirect('/login')


@app.route('/faq')
def faq():
    return render_template('/static/faq.html')

@app.route('/about')
def about():
	return render_template('/static/about.html')

@app.route('/iot')
def iot():
	return render_template('/static/iot.html')

@app.route('/backend')
def backend():
	return render_template('/static/backend.html')

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def errorpage(e):
	return render_template('/static/error.html')

def cleanup():
	try:
		cur.close()
	except Exception:
		pass

atexit.register(cleanup)

if __name__ == '__main__':
    socketio.run(app)
