from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import flask_login
import time
import MySQLdb

app = Flask(__name__)
Bootstrap(app)

db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                     user="carlos",         # your username
                     passwd="carlos",  # your password
                     db="map")        # name of the data base

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == "POST":
		with open('data', 'a') as f:
			f.write("--- POST FROM " + str(request.headers.get('User-Agent')) + " ---" + time.strftime("%H:%M:%S") + "\n")
			f.write(str(request.form) + "\n")
			for key in request.form:
				f.write("  " + str(key) + " - " + str(request.form[key]) + "\n")
                        print(str(request.headers))
                        print(str(request.form) + "\n\n")
		return "<html><body>Success!</body></html>"
	else:
		return render_template('index.html')

@app.route('/map')
def map():
	location_info = [{'name':'BTULab','coords':{'lat': 40.0076, 'lng': -105.2700}, 'desc': 'BTU Lab', 'id':1,}, {'name':'SOCLab', 'coords':{'lat': 40.0076, 'lng': -105.2618}, 'desc': 'SOC Lab', 'id':2}]
	cur = db.cursor()
	cur.execute("SELECT * FROM friends")
	for row in cur.fetchall():
	    print(row)
	return render_template('map.html', location_info=location_info)

@app.route('/login')
def login():
	return 0

