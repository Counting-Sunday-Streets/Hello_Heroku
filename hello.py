import os
import urlparse
import psycopg2
from flask import Flask, render_template, request
import calendar
import time
import collections
import scipy.integrate
import logging
import datetime

app = Flask(__name__)

###
### Pages
###

@app.route('/')
def home_page():
	return render_template('home_page.html')

@app.route('/count/', methods=['GET', 'POST'])
def hello():
	if request.method == "GET":
		return render_template('counter.html', data={"event": os.environ['CURRENT_EVENT']})
	else:
		post_to_postgres(request.form['buttonPedValue'], request.form['buttonBikeValue'], request.form['locationBox'])
		return render_template('counter.html', data={"event": os.environ['CURRENT_EVENT']})

@app.route('/createevent/', methods=['GET', 'POST'])
def create_event():
	if request.method == "GET":
		return render_template('create_event.html')
	else:
		conn = connect_postgres()
		cur = conn.cursor()

		epoch_starttime = time.mktime(datetime.datetime.strptime(request.form['event-starttime'], "%Y-%m-%dT%H:%M").timetuple())
		epoch_endtime = time.mktime(datetime.datetime.strptime(request.form['event-endtime'], "%Y-%m-%dT%H:%M").timetuple())

		cur.execute("INSERT INTO events (start_time, end_time, location, count_interval, entrances) VALUES (%s,%s,%s,%s,%s)",
			(epoch_starttime, epoch_endtime, request.form['event-name'], 900, request.form['event-entrances']))
		conn.commit()
		end_postgres(conn, cur)
		return render_template('create_event.html')

@app.route('/selectevent/', methods=['GET', 'POST'])
def select_event():
	if request.method == "GET":
		conn = connect_postgres()

		cur = conn.cursor()
		events = []
		cur.execute("SELECT * FROM events;")
		for event in cur.fetchall():
			events.append({"data": event})
		end_postgres(conn, cur)
		return render_template('select_event.html', events=events, data={"event": os.environ['CURRENT_EVENT']})
	else:
		os.environ['CURRENT_EVENT'] = request.form['event']
		start, end = get_times(os.environ['CURRENT_EVENT'])
		os.environ['START_TIME'] = str(start)
		os.environ['END_TIME'] = str(end)
		return os.environ['CURRENT_EVENT']

@app.route('/data/')
def get_data():
	totals = run_stats()
	num_entrances = len(totals.keys())
	sum_people = sum([pair[0] + pair[1] for pair in totals.values()])
	sum_ped = sum([pair[0] for pair in totals.values()])
	sum_cyc = sum([pair[1] for pair in totals.values()])

	data = []
	for location, total in totals.items():
		data.append({"loc": location, "tot": total})

	totals = {"total": str(int(sum_people * 25 / num_entrances))}
	totals["ped"] = str(int(sum_ped * 25 / num_entrances))
	totals["cyc"] = str(int(sum_cyc * 25 / num_entrances))
	return render_template("data.html", data=data, totals=totals, current={"event": os.environ['CURRENT_EVENT']})

def post_to_postgres(num_people, num_bikes, loc):
	conn = connect_postgres()
	
	cur = conn.cursor()

	cur.execute("INSERT INTO sessions (eid, time, location, count_people, count_bikes) VALUES (%s,%s,%s,%s,%s)", 
		(os.environ['CURRENT_EVENT'], calendar.timegm(time.gmtime()), loc, num_people, num_bikes))
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

	#SELECT time, count_people, count_bikes from sessions where eid= ***selected event***
	if request.method == "GET":
		return render_template('display_data.html', events=events,data=dict(eid=5, nump=3, numb=2))
	else:
		#post_to_postgres(request.form['buttonPedValue'], request.form['buttonBikeValue'])
		return render_template('display_data.html', events=events,data=dict(eid=0, nump=0, numb=0))
	end_postgres(conn, cur)

###
### STATS
###

def integrate_simps(points):
	"""
	Takes a list of tuples and integrates over them
	"""
	START_TIME = float(os.environ["START_TIME"])
	END_TIME = float(os.environ["END_TIME"])

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
	INTERVAL = int(os.environ["INTERVAL"])

	cur = conn.cursor()

	cur.execute("SELECT eid,time,location,count_people,count_bikes FROM sessions WHERE eid = %s;", (os.environ['CURRENT_EVENT']))
	
	data_people = collections.defaultdict(list)
	data_bikes = collections.defaultdict(list)
	for row in cur.fetchall():
		people = []
		bikes = []

		start_time = row[1] - INTERVAL
		rate_people = float(row[3]) / INTERVAL
		rate_bikes = float(row[4]) / INTERVAL

		people.extend([(start_time, rate_people),(row[1], rate_people)])
		bikes.extend([(start_time, rate_bikes), (row[1], rate_bikes)])

		data_people[row[2]].extend(people)
		data_bikes[row[2]].extend(bikes)

	end_postgres(conn, cur)
	return data_people, data_bikes

def run_stats():
	conn = connect_postgres()
	data_people, data_bikes = pull_results(conn)
	totals = collections.defaultdict(list)

	for location, data in data_people.items():
		totals[location].append(int(integrate_simps(data)))

	for location, data in data_bikes.items():
		totals[location].append(int(integrate_simps(data)))

	return totals

def get_times(event):
	conn = connect_postgres()
	cur = conn.cursor()

	cur.execute("SELECT start_time, end_time FROM events WHERE id = %s;", (os.environ['CURRENT_EVENT']))
	row = cur.fetchall()

	end_time = row[0][1]
	start_time = row[0][0]
	return start_time, end_time

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