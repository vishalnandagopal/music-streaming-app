from os import getenv
from os.path import dirname

from dotenv import load_dotenv
from flask import Flask, Response, flash, redirect, render_template
from flask import request as r
from flask import session as sesh
from icecream import ic

from flask_session import Session

from .database import check_password, check_user_exists, create_user, fetch_user_details

# from database import db

# Initialize Flask app
app = Flask(
    "Music Streaming App",
    template_folder=dirname(__file__) + "/templates",
    static_folder=dirname(__file__) + "/static",
)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_COOKIE_HTTPONLY"] = True

Session(app)


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
@app.route("/welcome", methods=["GET", "POST"])
def index():
    if r.method == "POST":
        return {"msg": "Welcome to this music streaming app"}
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if r.method == "POST":
        f = r.form
        
        if not {"username", "password", "user_type"}.issubset(f.keys()):
            return {"msg": "Malformed request"}, 400
        
        elif check_user_exists(f["username"]):
            if check_password(f["username"], f["password"]):
                user_type = int(f["user_type"])
                if user_type == fetch_user_details(f["username"])[3]:
                    # Password is correct, starting session
                    sesh["username"] = f["username"]
                    sesh["user_type"] = user_type

                    match user_type:
                        case 1:
                            return redirect("/player")
                        case 2:
                            return redirect("/creator_dashboard")
                        case 0:
                            return redirect("/admin")
                else:
                    flash("Tried to log in under wrong category")
            else:
                flash("Wrong password or non-existent user!")
        else:
            flash("User does not exist. Please register first")
            return redirect("/register")
    return render_template("login.html")


@app.route("/register_creator", methods=["GET"])
def register_creator():
    return render_template("register.html", mode="creator")


@app.route("/register_user", methods=["GET"])
def register_creator():
    return render_template("register.html", mode="user")


@app.route
@app.route("/register", methods=["GET", "POST"])
def register():
    if r.method == "POST":
        f = r.form
        user_type = int(f["type"])

        if create_user(f["username"], f["password"], f["name"], user_type):
            # User has been created succesfully
            flash("User created successfully. Try signing in")
            if user_type == 0:
                # If admin, redirect to admin login page
                return redirect("/login_admin")
            # Else, redirect to normal login page
            return redirect("/login")

        else:
            flash("Could not create user! Try again")
            return redirect("/register")

    return render_template("register.html", mode="user")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    sesh.clear()
    flash("Logged out sucessfully!")
    return redirect("/login")


@app.route("/player", methods=["GET"])
def player():
    if check_logged_in(sesh, 1):
        return render_template("player.html")

    flash(
        "You are not allowed to access that page. Try logging in with a different account"
    )
    return redirect("/logout")


@app.route("/creator_dashboard", methods=["GET"])
def creator_dashboard():
    if check_logged_in(sesh, 2):
        return render_template("creator_dashboard.html")
    flash(
        "You are not allowed to access that page. Try logging in with a different account"
    )
    return redirect("/logout")


def check_logged_in(sesh: dict, user_type: int):
    if "user_type" not in sesh or sesh["user_type"] != user_type:
        return False
    return True


if __name__ == "__main__":
    load_dotenv()

    port = int(getenv("PORT")) if getenv("PORT") else 8000
    debug = (getenv("DEBUG").casefold() if getenv("DEBUG") else None) in {
        "y",
        "yes",
        "t",
        "true",
        "True",
    }

    app.run(host="0.0.0.0", port=port, debug=debug)
