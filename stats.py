import scipy.integrate
import collections 
import urlparse
import os
import psycopg2

def integrate_simps(points):
	"""
	Takes a list of tuples and integrates over them
	"""
	y_val = [tup[1] for tup in points]
	x_val = [tup[0] for tup in points]

	return scipy.integrate.simps(y_val, x_val, 'avg')

def pull_results(conn):
	"""
	Queries the database and returns lists of tuple rows mapped to locations
	"""
	cur = conn.cursor()

	cur.execute("SELECT time,location,count_people,count_bikes FROM sessions;")
	
	data_map = collections.defaultdict(list)
	for row in cur.fetchall():
		data_map[row[1]].append((row[0], row[2], row[3]))

	cur.close()
	conn.close()
	return data_map

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

print pull_results(connect_postgres())