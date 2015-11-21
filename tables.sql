CREATE TABLE sessions (id SERIAL PRIMARY KEY, eid integer, time float, location text, count_people integer, count_bikes integer);

CREATE TABLE events (id SERIAL PRIMARY KEY, start_time float, location text, count_interval integer, entrances integer);