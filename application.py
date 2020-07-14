import os

from flask import Flask, session, render_template, redirect, request, url_for, g, jsonify, flash
from flask_session import Session
import sqlite3
from passlib.hash import pbkdf2_sha256
from helpers import login_required
from werkzeug.utils import secure_filename  # For the file uploads for flask
from flask import send_from_directory  # To see uploaded files from:https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
from decimal import Decimal, getcontext

app = Flask(__name__)
app.secret_key = "8635c8244367b39542sfj384qrfskda14233f934qfjnsdand87e06f" #Needed it for sessions for some reason
# UPLOAD_FOLDER = '/static/notes/athensuni/economics'  # Should be dynamic--> first ask for uni and then program
ALLOWED_EXTENSIONS = {'pdf'}  #'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc' for now only allow pdfs
UPLOAD_FOLDER = ""
uni_choice = ""
program_choice = ""
note_title = ""
user_info = ""
error_from_other_page = ""
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# The code above will limit the maximum allowed payload to 16 megabytes. If a larger file is transmitted, Flask will raise a RequestEntityTooLarge exception.
# For the notes upload from: https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
conn = sqlite3.connect('database.db', check_same_thread=False)  
db = conn.cursor()

@app.before_request  # From: https://www.youtube.com/watch?v=2Zz97NVbH0U&t=492s 
def before_request():  # Had to import g from flask. It creates a global variable so I can then reference a users info in other routes
    g.user = None

    if 'user_id' in session:
        user = db.execute("SELECT * FROM users WHERE user_id=:input", {"input": session['user_id']}).fetchone()  #returns a tuple
        # print(f"user:{user}")
        #fetchall returns a list of tuples
        g.user = user

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=("POST", "GET"))
def register():
    if request.method == "POST":
        session.pop('user_id', None)  #pros do that..

        input_username = request.form.get('username')
        input_email = request.form.get('email')
        input_password_safe = pbkdf2_sha256.hash(request.form.get('password'))
        input_confirm_password_safe = pbkdf2_sha256.hash(request.form.get('confirm_password'))
        if not input_username:
                error = 'Please enter an username!'
        elif not input_email:
                error = 'Please enter an email address!' 
        elif not input_password_safe:
            error = 'Please enter a password!'
        elif not input_confirm_password_safe:
            error = 'Please enter a confirmation password!'
        else:  # If there are no empty fields
            #db.execute("SELECT username FROM users WHERE username=:input", {"input": input_username}) #RETURNS:<sqlite3.Cursor object at 0x040EFEE0>
            username_check = db.execute("SELECT username FROM users WHERE username=:input", {"input": input_username}).fetchall()
            email_check = db.execute("SELECT email FROM users WHERE email=:input", {"input": input_email}).fetchall() #returns empty list
            if len(username_check) != 0:
                error = 'This username has already been taken. Please enter a different username.'
            elif len(email_check) != 0:  #email already exists
                error = 'This email address has already been taken. Please enter a different email address.'
            elif pbkdf2_sha256.verify(request.form.get('confirm_password'), input_password_safe) == False:  # If the passwords dont match
                error = "The confirmation password does not match the password you inserted!"
            else:  # If everything is good!
                error = "You were succesfully registered!"
                db.execute('''INSERT INTO users (
                            username, email, password) VALUES (?, ?, ?)''', (input_username,input_email, input_password_safe)).fetchone()
                conn.commit()  #not db.commit!!
                error = "Registration complete! You may now login."
                return redirect(url_for('login', error=error))
                # render_template("login.html", error= error)
        return render_template('register.html', error=error)
    
    else:  # If method == GET
        return render_template("register.html")
    
        
@app.route("/login", methods=("POST", "GET"))
def login():
    if request.method == "POST":
        input_username = request.form.get('username')
        input_password = request.form.get('password')
        session.pop('username', None)  #pros do that..
        if not input_username:
            error = 'Please enter a username!'
        elif not input_password:
            error = 'Please enter a password!'
        else:  # If both were given
            input_check = db.execute("SELECT * FROM users WHERE username=:input", {"input": input_username}).fetchone()  # Tuple
            #print(input_check)
            if input_check is None:  # if no username matched from the database
                error = "Incorrect username"
            elif pbkdf2_sha256.verify(input_password, input_check[3]) == False:  # If the passwords dont match
                error = "Wrong password"
            else:
                error = "You were sucesfully logged in!"
                print(input_check)
                user_id = input_check[0]
                session["user_id"] = user_id # Not sure if I need this here
                print(session["user_id"])
                return render_template('home.html', error=error)
                # return redirect(url_for('search', error=error))
        return render_template('login.html', error=error)
    
    else:  # If method == "GET"
        return render_template("login.html")


@app.route("/home")
# No login required
def home():
    return render_template("home.html")

# Select the uni and the program
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    global UPLOAD_FOLDER
    global uni_choice
    global program_choice
    global note_title
    if request.method == "GET":
        return render_template("sell.html")
    else:
        uni_choice = request.form.get("uni_choice")
        program_choice = request.form.get("program_choice")
        note_title = request.form.get("note_title")
        if program_choice is None:
            error = "You must choose a program before clicking 'Next'"
            return render_template("sell.html", error=error)
        elif not note_title:
            error = "You must choose a title for your notes! Users can search for you notes by it's title so try to give a meaningful one."
            return render_template("sell.html", error=error)
        UPLOAD_FOLDER = "static/notes/" + uni_choice + "/" + program_choice
        print(f"UPLOAD_FOLDER select: {UPLOAD_FOLDER}")
        # app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        session['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        print(f"SESSION UPLOAD_FOLDER select: {session['UPLOAD_FOLDER']}")
        return redirect("/upload-notes")
    # Create a directory in a known location to save files to.
    # uploads_dir = os.path.join(app.instance_path, 'uploads')
    # os.makedirs(uploads_dir, exists_ok=True)


@app.route('/upload-notes', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            full_filename = secure_filename(file.filename)
            print(full_filename)
            filename, file_extension = os.path.splitext(full_filename)
            print(filename)
            print(file_extension)
            global UPLOAD_FOLDER
            global uni_choice
            global program_choice
            global note_title
            app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
            db.execute("INSERT INTO notes_uploaded (uploader_id, filename, university, program, title) VALUES (?, ?, ?, ?, ?)", (g.user[0], full_filename, uni_choice, program_choice, note_title,))
            conn.commit()
            last_id = db.execute("SELECT last_insert_rowid()").fetchone()  # Returns a tuple (3,)
            # path_of_note = app.config['UPLOAD_FOLDER']
            path_of_note = UPLOAD_FOLDER
            id_of_file = str(last_id[0])
            saved_name = id_of_file + file_extension
            path_for_db = 'static/notes/' + uni_choice + '/' + program_choice+ '/' + saved_name
            db.execute("UPDATE notes_uploaded SET path=? WHERE note_id =?", (path_for_db, id_of_file))
            conn.commit()
            #todo: fix the where problem
            print("Inserted the path : {{ path_for_db }}")
            # uploads_dir = os.path.join(app.instance_path, 'uploads')
            uploads_dir = os.path.basename(path_of_note)
            os.makedirs(uploads_dir, exist_ok=True)

            # To save the notes file
            path_of_note = "C:/Users/belia/Desktop/CS50/final_project/" + path_of_note + "/" + saved_name
            print(f"Final path_of_note: {path_of_note}")
            # path_of_note_join = os.path.join("Users", "belia", "Desktop", "CS50", "final_project", UPLOAD_FOLDER, saved_name)
            # path_of_note_join = os.path.join("C:\\", "Users", "belia", "Desktop", "CS50", "final_project", "notes", uni_choice, program_choice, saved_name)
            path_of_note_join = os.path.join("C:\\", "Users", "belia", "Desktop", "CS50", "final_project", "static", "notes", uni_choice, program_choice, saved_name)
            path_of_note_join = os.path.join("\\static", "notes", uni_choice, program_choice, saved_name)
            path_of_note_join = os.path.relpath(path_of_note_join)
            print(f"Final path_of_note with join: {path_of_note_join}")
            # print(os.path.basename(path_of_note))
            # file.save(path_of_note_join)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_name))
            error = f"Congratulations! You succesfully uploaded the file: {full_filename}"
            # return redirect(url_for('uploaded_file', filename=filename))
            return render_template("/home.html", error=error)
    else:
        return render_template("upload-notes.html")

# ToDo: View your uploaded files and remove them if you want

@app.route("/account")
@login_required
def account():
    if not g.user:  # If the user is not in session, he needs to login (g.user was the global variable)
        return redirect(url_for('login'))
    global user_info
    user_info = db.execute("SELECT * FROM user_info WHERE user_id=?", (g.user[0],)).fetchone()
    global error_from_other_page
    # return redirect(url_for("account", user_info=user_info))
    return render_template('account.html', user_info=user_info, error=error_from_other_page)  # To do: check if i need the above 2 lines. Add an account tab


@app.route("/view_uploads")
@login_required
def view_uploads():
    notes_uploaded = db.execute("SELECT * FROM notes_uploaded WHERE uploader_id = ?", (g.user[0],)).fetchall()
    return render_template("/view_uploads.html", notes_uploaded=notes_uploaded)


@app.route("/edit-user-info/<variable>", methods=("POST", "GET"))
@login_required
def edit_variable(variable):
    global error_from_other_page
    # Need this if condition because I have different tables
    if variable == "username" or variable == "email":
        old_variable = db.execute("SELECT (%s) FROM users WHERE user_id=?" % (variable), (g.user[0],)).fetchall()
        old_variable = old_variable[0][0]
        if request.method == "GET":
            return render_template("/edit_user_info.html", variable=variable, old_variable=old_variable)
        else:
            input_variable = request.form.get(variable)
            duplicate_check = db.execute("SELECT * FROM users WHERE (%s)=?" % (variable), (input_variable,)).fetchall()
            # Check if nothing was submitted
            if not input_variable:
                error = "You cannot submit an empty field!"
                return render_template("/edit_user_info.html", error=error, variable=variable, old_variable=old_variable)

            # If the variable input already exists:
            elif (len(duplicate_check) != 0):
                error = "The " + variable + " you selected has already been taken. Please choose a different " + variable
                return render_template("/edit_user_info.html", error=error, variable=variable, old_variable=old_variable)

            # If the variable input is unique:
            db.execute("UPDATE users SET %s=? WHERE user_id=?" % variable, (input_variable, g.user[0],))
            error_from_other_page = "Your " + variable + " has been succesfully updated!"
            conn.commit()
            return redirect(url_for("account", error=error_from_other_page))

    # For all other varibles
    else:
        old_variable = db.execute("SELECT (%s) FROM user_info WHERE user_id=?" % variable, (g.user[0],)).fetchall()
        print(old_variable)
        old_variable = old_variable[0][0]
        print(old_variable)
        if request.method == "GET":
            return render_template("/edit_user_info.html", variable=variable, old_variable=old_variable)

        else:
            input_variable = request.form.get(variable)
            if not input_variable:
                error = "You cannot submit an empty field!"
                return render_template("/edit_user_info.html", error=error, variable=variable, old_variable=old_variable)

            # If the method is POST and the input is valid
            db.execute("UPDATE user_info SET %s=? WHERE user_id=?" % variable, (input_variable, g.user[0],))
            error_from_other_page = "Your " + variable + " has been succesfully updated!"
            conn.commit()
            return redirect(url_for("account", error=error_from_other_page))


@app.route("/search", methods=("GET", "POST"))
# No login required
def search():
    if request.method == "GET":
        return render_template("search.html")
    else:
        notes_title_input = request.form.get("notes_title_input")  # When left empty the output is empty ("")
        uni_choice = request.form.get("uni_choice")  # When left empty the output is None
        program_choice = request.form.get("program_choice")  # When left empty the output is None
        print(f"notes_title_input: {notes_title_input}")
        print(f"uni_choice: {uni_choice}")  
        print(f"program_choice: {program_choice}")


        # If the user did not submit any search criteria
        if not notes_title_input and uni_choice is None:
            query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                                users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                                user_info ON users.user_id = user_info.user_id""").fetchall()
            print(query)
            print("case1")
            return render_template("note_query.html", query = query)  #redirect(url_for("book_query", query = query)) WORKED!


        # If the only criteria was the notes title
        elif uni_choice is None:
            query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                            users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                            user_info ON users.user_id = user_info.user_id WHERE notes_uploaded.title LIKE ?""", ('%'+notes_title_input+'%',)).fetchall() 
            print(query)
            print("case2")
            return render_template("note_query.html", query = query)  #redirect(url_for("book_query", query = query)) WORKED!


        # If the only criteria was the university    
        elif not notes_title_input and program_choice is None:
            # If the selection was "Any university" univeristy
            if uni_choice == "any":
                print("case3")
                query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                                users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                                user_info ON users.user_id = user_info.user_id""").fetchall()
                return render_template("note_query.html", query = query)
            else:
                print("case3")
                query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                                users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                                user_info ON users.user_id = user_info.user_id WHERE notes_uploaded.university=?""", (uni_choice,)).fetchall()                
                return render_template("note_query.html", query = query)


        # If the only criteria was the title and the university
        elif program_choice is None:
            if uni_choice == "any":
                print("case4")
                query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                                users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                                user_info ON users.user_id = user_info.user_id WHERE 
                                notes_uploaded.title LIKE ?""", ('%'+notes_title_input+'%',)).fetchall()
                return render_template("note_query.html", query = query)
            else:
                query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                                users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                                user_info ON users.user_id = user_info.user_id WHERE 
                                notes_uploaded.title LIKE ? AND 
                                notes_uploaded.university=?""", ('%'+notes_title_input+'%', uni_choice,)).fetchall()
                print("case4")
                return render_template("note_query.html", query = query)


        # If the only criteria was the university and the program
        elif not notes_title_input:
            if uni_choice == "any" and program_choice == "any":
                print("case5")
                query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                                users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                                user_info ON users.user_id = user_info.user_id""").fetchall()
                return render_template("note_query.html", query = query)
            elif uni_choice == "any":
                print("case5")
                query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                                users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                                user_info ON users.user_id = user_info.user_id WHERE 
                                notes_uploaded.program=?""",(program_choice,)).fetchall()
                return render_template("note_query.html", query = query)
            elif program_choice == "any":
                print("case5")
                query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                                users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                                user_info ON users.user_id = user_info.user_id WHERE 
                                notes_uploaded.university=?""",(uni_choice,)).fetchall()
                return render_template("note_query.html", query = query)
            else:
                print("case5")
                query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                                users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                                user_info ON users.user_id = user_info.user_id WHERE 
                                notes_uploaded.university=? AND
                                notes_uploaded.program=?""",(uni_choice, program_choice,)).fetchall()
                return render_template("note_query.html", query = query)


        # If all three criteria were given
        else:
            print("case6")
            query = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                            users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                            user_info ON users.user_id = user_info.user_id WHERE 
                            notes_uploaded.title LIKE ? AND
                            notes_uploaded.university=? AND
                            notes_uploaded.program=?""",('%'+notes_title_input+'%', uni_choice, program_choice,)).fetchall()
            return render_template("note_query.html", query = query)


@app.route("/search_results")
# No login required
def note_query(query):
    # Return a list of titles where the search results match
    return render_template("note_query.html", query = query)


@app.route("/view_profile/<user_id>")
@login_required
def view_profile(user_id):
    pass
# Todo: allow people to view someones profile
# Todo: allow people to upload a picture
# Todo: Make a leaderboard with all the notes sellers


@app.route("/note_details/<note_id>", methods=("POST", "GET"))
# Returns details about a single note
@login_required
def note_details(note_id):
    note_details = db.execute("""SELECT * FROM notes_uploaded INNER JOIN 
                            users ON notes_uploaded.uploader_id = users.user_id INNER JOIN
                            user_info ON users.user_id = user_info.user_id WHERE 
                            notes_uploaded.note_id=?""",(note_id,)).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE note_id=?", (note_id,)).fetchall()

    # To calculate the average review score
    sum_of_scores = 0
    num_of_reviews = 0
    for review in reviews:
        sum_of_scores += review[5]
        num_of_reviews += 1
    getcontext().prec = 2
    average_review_score = Decimal(sum_of_scores) / Decimal(num_of_reviews)
    print(average_review_score)

    if request.method == "GET":
        reviews = db.execute("SELECT * FROM reviews WHERE note_id=?", (note_id,)).fetchall()
        return render_template("note_details.html", note_details = note_details, reviews = reviews, average_review_score=average_review_score, num_of_reviews=num_of_reviews)


    # If the user submitted a review
    else:
        pass
        # First need to check if a review had already been submitted by this user for this book
        check = db.execute("SELECT * FROM reviews WHERE note_id=? AND reviewer_id=?", (note_id, g.user[0],)).fetchall()
        print(f"Post check {check}")
        if len(check) == 0:
            # Todo: dynamically check if the user has bought or not bought the review.. I have hardcoded "not bought" for now
            db.execute("INSERT INTO reviews (note_id, reviewer_id, username, review_score, bought, opinion) VALUES (?,?,?,?,?,?)", (note_id, g.user[0], g.user[1], request.form.get('rating'), "not bought", request.form.get("opinion")))
            conn.commit()
            error = "Your review was submitted succesfully!"
            return render_template("search.html", error = error)
        else:
            error = "You have already submitted a review for this book. Only one is allowed."
            return render_template("search.html", error = error)


@app.route("/logout")
@login_required
def logout():
    [session.pop(key) for key in list(session.keys())]
    session.clear()  # So that if i logout I need to put my password in to login again! Otherwise I could access anything (/search etc.)
    error = "You were succesfully logged out!"
    return render_template('index.html', error=error)
    # return redirect(url_for('index', error=error))


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@app.errorhandler(500)
def something_went_wrong(e):
    # note that we set the 404 status explicitly
    return render_template('500.html'), 500

# $env:FLASK_APP= "application.py"
# $env:DATABASE_URL= "postgres://bjjphsnuxjabfm:0802b24ffd3e4d7a240cb35089d4969cd9b5e54cdfb8c6f45848fd18523764a3@ec2-54-247-94-127.eu-west-1.compute.amazonaws.com:5432/d74hfp6ao6b1hb"
if __name__=='__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    #app.run(debug=True)
    app.run(debug=True)
    # use_reloader=False,