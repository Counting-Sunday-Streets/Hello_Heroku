import scipy.integrate
import collections 
import urlparse
import os
import psycopg2

INTERVAL = int(os.environ["INTERVAL"])
START_TIME = int(os.environ["START_TIME"])

def integrate_simps(points):
	"""
	Takes a list of tuples and integrates over them
	"""
	y_val = [tup[1] for tup in points]
	x_val = [tup[0] for tup in points]

	if START_TIME not in x_val:
		x_val.insert(0, START_TIME)
		y_val.insert(0, 0)

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

	cur.close()
	conn.close()
	return data_people, data_bikes

def run_stats():
	# construct a conn
	data_people, data_bikes = pull_results(conn)
	totals = collections.defaultdict(list)

	for location, data in data_people.items():
		totals[location].append(integrate_simps(data))

	for location, data in data_bikes.items():
		totals[location].append(integrate_simps(data))

	return totals