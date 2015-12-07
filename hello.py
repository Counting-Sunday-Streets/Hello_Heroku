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
### EVENT VARIABLES
###
CURRENT_EVENT = 0
START_TIME = 0
END_TIME = 14400
INTERVAL = 900

###
### Pages
###

@app.route('/')
def home_page():
	return render_template('home_page.html')

@app.route('/count/', methods=['GET', 'POST'])
def hello():
	env = get_current_event()
	if request.method == "GET":
		return render_template('counter.html', data={"event": env[0]})
	else:
		post_to_postgres(request.form['buttonPedValue'], request.form['buttonBikeValue'], request.form['locationBox'])
		return render_template('counter.html', data={"event": env[0]})

@app.route('/createevent/', methods=['GET', 'POST'])
def create_event():
	env = get_current_event()
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
		events = []
		cur.execute("SELECT * FROM events;")
		for event in cur.fetchall():
			events.append({"data": event})
		end_postgres(conn, cur)
		return render_template('select_event.html', events=events, data={"event": env[0]}, add={'add': False})

@app.route('/selectevent/', methods=['GET', 'POST'])
def select_event():
	env = get_current_event()
	if request.method == "GET":
		conn = connect_postgres()

		cur = conn.cursor()
		events = []
		cur.execute("SELECT * FROM events;")
		for event in cur.fetchall():
			events.append({"data": event})
		end_postgres(conn, cur)
		return render_template('select_event.html', events=events, data={"event": env[0]}, add={'add': False})
	else:
		set_event(request.form['event'])

		conn = connect_postgres()
		cur = conn.cursor()

		events = []
		cur.execute("SELECT * FROM events;")
		for event in cur.fetchall():
			events.append({"data": event})
		end_postgres(conn, cur)
		return render_template('select_event.html', events=events, data={"event": request.form['event']}, add={'add': True})

@app.route('/data/')
def get_data():
	env = get_current_event()
	totals = run_stats()
	num_entrances = len(totals.keys())
	if num_entrances != 0:
		sum_people = sum([pair[0] + pair[1] for pair in totals.values()])
		sum_ped = sum([pair[0] for pair in totals.values()])
		sum_cyc = sum([pair[1] for pair in totals.values()])

		data = []
		for location, total in totals.items():
			data.append({"loc": location, "tot": total})

		totals = {"total": str(int(sum_people * 25 / num_entrances))}
		totals["ped"] = str(int(sum_ped * 25 / num_entrances))
		totals["cyc"] = str(int(sum_cyc * 25 / num_entrances))
		return render_template("data.html", data=data, totals=totals, current={"event": env[0]})
	else:
		return render_template("data.html", data=[], totals={'total':0, 'ped':0, 'cyc':0}, current={"event": env[0]})

def post_to_postgres(num_people, num_bikes, loc):
	env = get_current_event()
	conn = connect_postgres()
	cur = conn.cursor()

	cur.execute("INSERT INTO sessions (eid, time, location, count_people, count_bikes) VALUES (%s,%s,%s,%s,%s)", 
		(env[0], calendar.timegm(time.gmtime()), loc, num_people, num_bikes))
	conn.commit()
	end_postgres(conn, cur)

###
### STATS
###

def integrate_simps(points):
	"""
	Takes a list of tuples and integrates over them
	"""
	env = get_current_event()

	y_val = [tup[1] for tup in points]
	x_val = [tup[0] for tup in points]

	if env[1] not in x_val:
		x_val.insert(0, env[1])
		y_val.insert(0, 0)

	if env[2] not in x_val:
		x_val.append(env[2])
		y_val.append(0)

	return scipy.integrate.simps(y_val, x_val, 'avg')

def pull_results(conn):
	"""
	Queries the database and returns lists of tuple rows mapped to locations
	"""
	env = get_current_event()

	cur = conn.cursor()

	cur.execute("SELECT eid,time,location,count_people,count_bikes FROM sessions WHERE eid = %s;", (env[0]))
	
	data_people = collections.defaultdict(list)
	data_bikes = collections.defaultdict(list)
	for row in cur.fetchall():
		people = []
		bikes = []

		start_time = row[1] - env[3]
		rate_people = float(row[3]) / env[3]
		rate_bikes = float(row[4]) / env[3]

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

def set_event(id):
	conn = connect_postgres()
	cur = conn.cursor()

	cur.execute("SELECT * FROM events WHERE id=%s", (id,))
	current = cur.fetchall()
	cur.execute("UPDATE current SET current_event=%s, start_time=%s, end_time=%s, interval=900", 
		(current[0][0], current[0][1], current[0][2]))
	conn.commit()
	end_postgres(conn, cur)

def get_current_event():
	conn = connect_postgres()
	cur = conn.cursor()

	cur.execute("SELECT * FROM current;")
	current = cur.fetchall()
	end_postgres(conn, cur)
	return current[0][0], current[0][1], current[0][2], current[0][3]

if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0')