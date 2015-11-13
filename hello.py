import os
import urlparse
import psycopg2
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def hello():
	if request.method == "GET":
		return render_template('index.html')
	else:
		post_to_postgres(request.form['buttonPedValue'], request.form['buttonBikeValue'])
		return render_template('index.html')

@app.route('/data/')
def get_data():
	return str(get_from_postgres());

def post_to_postgres(num_people, num_bikes):
	conn = psycopg2.connect("dbname=d903vmg658ksh1 user=navthyjfrkmxvh password=1hup-6RLTPuHvpnHpQ9Zte9pcC host=ec2-107-20-223-116.compute-1.amazonaws.com")

	cur = conn.cursor()

	cur.execute("INSERT INTO sessions (eid, time, location, count_people, count_bikes) VALUES (%s,%s,%s,%s,%s)", (1, str(datetime.now()), "location", num_people, num_bikes))
	conn.commit()
	cur.close()
	conn.close()

def get_from_postgres():
	conn = psycopg2.connect("dbname=d903vmg658ksh1 user=navthyjfrkmxvh password=1hup-6RLTPuHvpnHpQ9Zte9pcC host=ec2-107-20-223-116.compute-1.amazonaws.com")

	cur = conn.cursor()
	data = []
	cur.execute("SELECT * FROM sessions")
	
	for record in cur:
		data.append(record)

	cur.close()
	conn.close()
	return data

if __name__ == '__main__':
	app.debug = True
	app.run()