import sqlite3

f = open("schema.sql")
db = sqlite3.connect("twitter.db")
db.executescript(f.read())