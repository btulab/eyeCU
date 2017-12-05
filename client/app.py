from flask import Flask, render_template, request, redirect, session
# from flask_bootstrap import Bootstrap
import flask_login
import time
import MySQLdb
import ConfigParser
import os

app = Flask(__name__)
app.secret_key = os.urandom(12)
# Bootstrap(app)

dbcreds = ConfigParser.ConfigParser()
dbcreds.read('db.cfg')
db = MySQLdb.connect(host=dbcreds.get('database', 'host'),
                     user=dbcreds.get('database', 'user'),
                     passwd=dbcreds.get('database', 'passwd'),
                     db=dbcreds.get('database', 'db'))

last_update_dict = {"5C:CF:7F:AE:D9:65": 0} #used to store the last update recieved from a device

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == "POST":
		if request.form['MAC'] in last_update_dict:
			if (time.time() - last_update_dict[request.form['MAC']]) < 300:
				return "Too Many Requests."
			else:
				last_update_dict[request.form['MAC']] = time.time()
				print(last_update_dict)
		else:
			return "Could not verify MAC."

		print("--- POST FROM " + str(request.headers.get('User-Agent')) + " ---" + time.strftime("%H:%M:%S"))
		for key in request.form:
			print("  " + str(key) + " - " + str(request.form[key]))
		return "Success!"
	else:
		return render_template('index.html')

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

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == "POST":
		# for key in request.form:
		# 	print(key, str(request.form[key]))
		username = request.form["username"] or "null"
		password = request.form["password"] or "null"
		if str(username) == "eyeCU_administrator" and str(password) == "eyeTPsecurity":
			session['authenticated'] = True
			return redirect('/')
		else:
			return render_template("login.html")
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
				print insert_string
				cur.execute(insert_string)
				db.commit()
				return "Success"
			elif request.method == "GET":
				return render_template('display_add_device.html')
		else:
			return redirect('/login')
	else:
		return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
