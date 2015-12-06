CREATE TABLE sessions (id SERIAL PRIMARY KEY, eid integer, time float, location text, count_people integer, count_bikes integer);

CREATE TABLE events (id SERIAL PRIMARY KEY, start_time float, end_time float, location text, count_interval integer, entrances integer);

INSERT INTO events (start_time, end_time, location, count_interval, entrances) VALUES (0, 14400, "Staggered", 900, 25);
INSERT INTO sessions (eid, time, location, count_people, count_bikes) VALUES (2, 900, 1, 0, 0);