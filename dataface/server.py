from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import flask_login

app = Flask(__name__)
Bootstrap(app)

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == "POST":
		with open('data', 'w') as f:
			f.write(str(request.form))
	return render_template('index.html')

@app.route('/map')
def map():
	return render_template('map.html')

@app.route('/login')
def login():
	return 0

