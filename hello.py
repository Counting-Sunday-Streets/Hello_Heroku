import os
import urlparse
import psycopg2
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def hello():
	if request.method == "GET":
		return render_template('index.html')
	else:
		post_to_postgres(request.form['num_people'])
		return "Success!"

def post_to_postgres(num_people):
	urlparse.uses_netloc.append("postgres")
	url = urlparse.urlparse(os.environ["DATABASE_URL"])

	conn = psycopg2.connect(
    	database=url.path[1:],
    	user=url.username,
    	password=url.password,
    	host=url.hostname,
    	port=url.port
	)
	#conn = psycopg2.connect("dbname=count user=alex password=engi120 host=localhost")

	cur = conn.cursor()

	cur.execute("INSERT INTO count VALUES (%s)", (num_people,))
	conn.commit()
	cur.close()
	conn.close()


if __name__ == '__main__':
	app.debug = True
	app.run()