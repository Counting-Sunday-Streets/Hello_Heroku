import os
import urlparse
import psycopg2
from flask import Flask, render_template, request
import calendar
import time

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
	conn = connect_postgres()
	
	cur = conn.cursor()

	cur.execute("INSERT INTO sessions (eid, time, location, count_people, count_bikes) VALUES (%s,%s,%s,%s,%s)", (1, calendar.timegm(time.gmtime()), "location", num_people, num_bikes))
	conn.commit()
	cur.close()
	conn.close()

def get_from_postgres():
	conn = connect_postgres()

	cur = conn.cursor()
	data = []
	cur.execute("SELECT * FROM sessions")
	
	for record in cur:
		data.append(record)

	cur.close()
	conn.close()
	return data

def connect_postgres():
	urlparse.uses_netloc.append("postgres")
	url = urlparse.urlparse(os.environ["DATABASE_URL"])

	conn = psycopg2.connect(
    	database=url.path[1:],
    	user=url.username,
    	password=url.password,
    	host=url.hostname,
    	port=url.port)
	return conn

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')