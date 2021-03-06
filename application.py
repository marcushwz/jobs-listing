import os

from flask import Flask, session, redirect, render_template, request, flash, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://ypvuuadaexvgmf:4fcf02037d868398ac646f6d3cb05ca4b0ca1ccc4ff055b89fdc80fa5147d149@ec2-23-23-182-18.compute-1.amazonaws.com:5432/d2hg9oifn1sa61", pool_size=10, max_overflow=20)
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    if session.get("user_id"):
        rows = db.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
        return render_template("index.html", rows=rows)
    return render_template("index.html")

@app.route("/login", methods= ["GET", "POST"])
def login():
    """ This route handles user login """
    if request.method == "GET":
        return render_template("login.html")
    else:
        row = db.execute("SELECT * FROM users WHERE username=:username", {"username": request.form.get("username")}).fetchone()
        print(row["password"])
        # Check whether username exists in database
        if row == None:
            flash(u"Username does not exists.", "warning")
            return redirect(request.url)
        else:
            # Check the input password is correct or not
            if not check_password_hash(row["password"], request.form.get("password")):
                flash(u"Incorrect password", "danger")
                return redirect(request.url)
        
        # For successfully log in user, save their user id in session
        session["user_id"] = row["id"]
        return redirect("/")

@app.route("/register", methods=["GET","POST"])
def register():
    """ This route is used for users registration """
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        row = db.execute("SELECT * FROM users WHERE username=:username", {"username": username}).fetchone()

        # Check whether username already exists in database
        if row != None:
            flash(u"Username is taken, please try another one.", "warning")
            return redirect(request.url)
        
        # Check input passwords match
        if request.form.get("password") != request.form.get("password2"):
            flash(u"Passwords do not match.", "danger")
            return redirect(request.url)
        
        # Insert user details into table "users"
        hash_password = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)", {"username": request.form.get("username"), "email": request.form.get("email"), "password":hash_password})
        db.commit()
        flash(u"Account created successfully. Please login here!", "success")
        return redirect("/login")

@app.route("/logout")
def logout():
    """ This route handles user log out """
    # Clear all the session
    session.clear()
    return redirect("/")

@app.route("/addJob", methods=["GET","POST"])
def addJob():
    """ This route is used to add new job to the database """
    if request.method == "GET":
        return render_template("addJob.html")
    else:
        db.execute("INSERT INTO jobs (company, title, description, requirement) VALUES (:company, :title, :description, :requirement)", {"company":request.form.get("company"), "title":request.form.get("title"), "description": request.form.get("description"), "requirement":request.form.get("requirement")})
        db.commit()
        return redirect("/")

@app.route("/recommended", methods=["GET","POST"])
def recommended():
    """ This route is used to show recommended jobs for users """
    if request.method == "GET":
        return render_template("recommended.html")
    else:
        return redirect("/")

@app.route("/search", methods=["GET"])
def search():
    """ This route handle the job search """
    if request.method == "GET":
        title = '%'
        title += request.args.get("search")
        title += '%'
        rows = db.execute("SELECT * FROM jobs WHERE LOWER(title) LIKE LOWER(:title) ORDER BY id DESC", 
                            {"title": title}).fetchall()
        print(len(rows))
        if len(rows) == 0:
            flash(u"There is no job with this title", "warning")
            return render_template("search.html", rows=rows)

        return render_template("search.html", rows=rows)