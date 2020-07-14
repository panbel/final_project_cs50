from functools import wraps
from flask import g, request, redirect, url_for, Flask
import sqlite3
import datetime

# From https://flask.palletsprojects.com/en/1.0.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


conn = sqlite3.connect('database.db', check_same_thread=False)
db = conn.cursor()

db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, username VARCHAR, email VARCHAR NOT NULL, password VARCHAR NOT NULL)")
             #AUTOINCREMENT is to prevent the reuse of ROWIDs from previously deleted rows.

db.execute("CREATE TABLE IF NOT EXISTS user_info (user_id INTEGER NOT NULL PRIMARY KEY, gender VARCHAR, age INTEGER, university VARCHAR, program VARCHAR, facebook VARCHAR, instagram VARCHAR, linkdin VARCHAR, etos INTEGER, FOREIGN KEY (user_id) REFERENCES users (user_id))")


db.execute("CREATE TABLE IF NOT EXISTS notes_uploaded (note_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, uploader_id INTEGER NOT NULL, upload_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, filename VARCHAR NOT NULL, university VARCHAR NOT NULL, program VARCHAR NOT NULL, FOREIGN KEY(uploader_id) REFERENCES users(user_id))")
# db.execute("CREATE TABLE IF NOT EXISTS friends (friend")


db.execute("""CREATE TABLE IF NOT EXISTS reviews (review_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, note_id INTEGER NOT NULL, 
        reviewer_id INTEGER NOT NULL, submission_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, username VARCHAR NOT NULL, review_score TEXT NOT NULL,  bought TEXT NOT NULL, opinion TEXT, FOREIGN KEY(note_id) REFERENCES notes_uploaded (note_id), FOREIGN KEY (reviewer_id) REFERENCES users (user_id))
        """)