import os
import urlparse
import psycopg2
from flask import Flask, render_template, request
import calendar
import time
import collections
import scipy.integrate
import logging

app = Flask(__name__)

###
###  PAGES
###
@app.route('/', methods=['GET', 'POST'])
def hello():
	if request.method == "GET":
		return render_template('counter.html')
	else:
		post_to_postgres(request.form['buttonPedValue'], request.form['buttonBikeValue'])
		return render_template('counter.html')

@app.route('/createevent/')
def create_event():
	return render_template('create_event.html')

@app.route('/selectevent/')
def select_event():
	conn = connect_postgres()

	cur = conn.cursor()
	events = []
	cur.execute("SELECT distinct id FROM events")
	for eid in cur.fetchall():
		app.logger.info(eid)
		events.append(dict(text=eid[0]))
	app.logger.info(events)
	return render_template('select_event.html', events=events)

@app.route('/data/')
def get_data():
	totals = run_stats()
	PAGE = ""

	for location, total in totals.items():
		PAGE += location 
		PAGE += " - " 
		PAGE += "People: " 
		PAGE += str(total[0])
		PAGE += ", Bikes: " 
		PAGE += str(total[1])
		PAGE += "\n"
	return PAGE

def post_to_postgres(num_people, num_bikes):
	conn = connect_postgres()
	
	cur = conn.cursor()

	cur.execute("INSERT INTO sessions (eid, time, location, count_people, count_bikes) VALUES (%s,%s,%s,%s,%s)", (1, calendar.timegm(time.gmtime()), 1, num_people, num_bikes))
	conn.commit()
	end_postgres(conn, cur)

@app.route('/displaydata/', methods=['GET', 'POST'])
def display_data():
	conn = connect_postgres()

	cur = conn.cursor()
	events = []
	cur.execute("SELECT distinct id FROM events")
	for eid in cur.fetchall():
		events.append(dict(text=eid))


	if request.method == "GET":
		return render_template('display_data.html', events=events,data=dict(eid=5, nump=3, numb=2))
	else:
		#post_to_postgres(request.form['buttonPedValue'], request.form['buttonBikeValue'])
		return render_template('display_data.html', events=events,data=dict(eid=0, nump=0, numb=0))
	end_postgres(conn, cur)

###
### STATS
###

INTERVAL = int(os.environ["INTERVAL"])
START_TIME = int(os.environ["START_TIME"])
END_TIME = int(os.environ["END_TIME"])

def integrate_simps(points):
	"""
	Takes a list of tuples and integrates over them
	"""
	y_val = [tup[1] for tup in points]
	x_val = [tup[0] for tup in points]

	if START_TIME not in x_val:
		x_val.insert(0, START_TIME)
		y_val.insert(0, 0)

	if END_TIME not in x_val:
		x_val.append(END_TIME)
		y_val.append(0)

	return scipy.integrate.simps(y_val, x_val, 'avg')

def pull_results(conn):
	"""
	Queries the database and returns lists of tuple rows mapped to locations
	"""
	cur = conn.cursor()

	cur.execute("SELECT time,location,count_people,count_bikes FROM sessions;")
	
	data_people = collections.defaultdict(list)
	data_bikes = collections.defaultdict(list)
	for row in cur.fetchall():
		people = []
		bikes = []

		start_time = row[0] - INTERVAL
		rate_people = float(row[2]) / INTERVAL
		rate_bikes = float(row[3]) / INTERVAL

		people.extend([(start_time, rate_people),(row[0], rate_people)])
		bikes.extend([(start_time, rate_bikes), (row[0], rate_bikes)])

		data_people[row[1]].extend(people)
		data_bikes[row[1]].extend(bikes)

	end_postgres(conn, cur)
	return data_people, data_bikes

def run_stats():
	conn = connect_postgres()
	data_people, data_bikes = pull_results(conn)
	totals = collections.defaultdict(list)

	for location, data in data_people.items():
		totals[location].append(integrate_simps(data))

	for location, data in data_bikes.items():
		totals[location].append(integrate_simps(data))

	return totals

###
### DATABASE CONNECTION MAINTAINANCE
###

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

def end_postgres(conn, cur):
	cur.close()
	conn.close()

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')