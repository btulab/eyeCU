from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import flask_login
import time

app = Flask(__name__)
Bootstrap(app)

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
	return render_template('map.html')

@app.route('/login')
def login():
	return 0

