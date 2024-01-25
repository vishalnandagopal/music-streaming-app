from os import getenv
from os.path import splitext
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, flash, get_flashed_messages, jsonify, redirect, render_template
from flask import request as r
from flask import session as sesh
from werkzeug.utils import secure_filename

from flask_session import Session

from .database import (
    Song,
    add_song_to_db,
    add_to_blacklist,
    check_password,
    check_user_exists,
    create_user,
    delete_song_from_db,
    fetch_song_details_from_db,
    fetch_user_details,
    get_available_playlists,
    get_available_songs,
    get_number_of_creators,
    get_number_of_listeners,
    update_song_details_in_db,
)

# Initialize Flask app
app = Flask("Music Streaming App")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["UPLOAD_EXTENSIONS"] = [
    ".mp3",
    ".mp4",
    ".ogg",
    ".wav",
    ".flac",
    ".aac",
    ".wma",
    ".m4a",
]
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 10


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

        if not {"username", "pw", "user_type"}.issubset(f.keys()):
            return {"msg": "Malformed request"}, 400

        elif check_user_exists(f["username"]):
            if check_password(f["username"], f["pw"]):
                user_type = int(f["user_type"])
                if user_type == fetch_user_details(f["username"])[3]:
                    # Password is correct, starting session
                    sesh["username"] = f["username"]
                    sesh["user_type"] = user_type

                    match user_type:
                        case 1:
                            return redirect("/player")
                        case 2:
                            return redirect("/creator")
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


@app.route
@app.route("/register", methods=["GET", "POST"])
def register():
    if r.method == "POST":
        f = r.form

        if not {"username", "pw", "user_type"}.issubset(f.keys()):
            return {"msg": "Malformed request"}, 400

        user_type = int(f["user_type"])

        if create_user(f["username"], f["pw"], f["name"], user_type):
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


@app.route("/register_creator", methods=["GET"])
def register_creator():
    return render_template("register.html", mode="creator")


@app.route("/register_user", methods=["GET"])
def register_user():
    return render_template("register.html", mode="user")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    previously_flashed_messages = get_flashed_messages()
    sesh.clear()
    map(flash, previously_flashed_messages)
    return redirect("/login")


@app.route("/upload_song", methods=["GET", "POST"])
def upload_song():
    """accept and process a music file sent by the user, and send it to the add_song_to_db function. Return a success or failure message the"""

    # Check admin or creator
    if not (check_logged_in(sesh, 2) or check_logged_in(sesh, 0)):
        flash(
            "You are not allowed to access that page. Try logging in with a different account"
        )
        return redirect("/logout")

    if r.method == "GET":
        return render_template("upload_song.html", name=sesh["username"])

    music_file = r.files["file"]

    if music_file.filename == "":
        return {"msg": "No filename"}, 400

    music_file.filename = secure_filename(music_file.filename)
    # Checking if file is allowed
    if splitext(music_file.filename)[1] not in app.config["UPLOAD_EXTENSIONS"]:
        return {"msg": "Invalid file extension"}, 400

    # Checking other fields
    f = r.form
    if not {"name", "artist", "album", "genre", "year", "lyrics"}.issubset(f.keys()):
        return {"msg": "Malformed request. Missing keys"}, 400

    if add_song_to_db(
        Song(
            [
                str(uuid4()),
                f["name"],
                f["artist"],
                f["album"],
                f["genre"],
                f["year"],
                f["lyrics"],
                sesh["username"],
            ],
        ),
        music_file,
    ):
        flash("Song uploaded successfully")
        return redirect("/creator")
    flash("Could not upload song")
    return redirect("/creator")


@app.route("/fetch_song_details", methods=["POST"])
def fetch_song_details():
    """Fetch song details from the database"""

    d = r.json

    if not {"music_id"}.issubset(d.keys()):
        return {"msg": "Malformed request"}, 400
    song_details = fetch_song_details_from_db(d["music_id"])

    return jsonify(song_details.__dict__)


@app.route("/blacklist", methods=["GET", "POST"])
def blacklist():
    """Blacklist some text into the database"""

    if not check_logged_in(sesh, 0):
        flash(
            "You are not allowed to access that page. Try logging in with a different account"
        )
        return redirect("/logout"), 403

    if r.method == "POST":
        f = r.form

        if not {"text"}.issubset(f.keys()):
            return {"msg": "Malformed request"}, 400

        add_to_blacklist(f["text"])
        flash(f"Blacklisted {f['text']} successfully")

    return render_template("blacklist.html")


@app.route("/add_to_playlist", methods=["GET", "POST"])
def add_to_playlist():
    if "p" not in sesh:
        sesh["playlist"] = [r.form["music_id"]]
    else:
        sesh["playlist"].append(r.form["music_id"])
    return redirect("/player")


@app.route("/player", methods=["GET", "POST"])
def player():
    if check_logged_in(sesh, 1):
        return render_template(
            "player.html",
            available_songs=get_available_songs(),
            available_playlists=get_available_playlists(sesh["username"]),
        )

    flash(
        "You are not allowed to access that page. Try logging in with a different account"
    )

    return redirect("/logout")


@app.route("/creator", methods=["GET", "POST"])
def creator():
    if check_logged_in(sesh, 2):
        available_songs = list(
            filter(
                lambda song: song.owner == sesh["username"],
                get_available_songs(),
            ),
        )
        return render_template("creator.html", available_songs=available_songs)
    flash(
        "You are not allowed to access that page. Try logging in with a different account"
    )
    return redirect("/logout")


@app.route("/edit_song_details/<music_id>", methods=["GET", "POST"])
def edit_song_details(music_id: str):
    if not (check_logged_in(sesh, 2) or check_logged_in(sesh, 0)):
        flash(
            "You are not allowed to access that page. Try logging in with a different account"
        )
        return redirect("/logout")
    song = fetch_song_details_from_db(music_id)
    if song.owner == sesh["username"] or sesh["user_type"] == 0:
        if r.method == "POST":
            f = r.form
            if not {"name", "artist", "album", "genre", "year", "lyrics"}.issubset(
                f.keys()
            ):
                return {"msg": "Malformed request. Not all required keys present"}, 400
            print(f["name"])
            if update_song_details_in_db(
                music_id,
                f["name"],
                f["artist"],
                f["album"],
                f["genre"],
                f["year"],
                f["lyrics"],
            ):
                flash("Updated successfully")
            else:
                flash("Could not update song")
            if sesh["user_type"] == 0:
                return redirect("/admin")
            return redirect("/creator")
        return render_template("edit_song_details.html", song=song)


@app.route("/delete_song/<music_id>", methods=["GET", "POST"])
def delete_song(music_id: str):
    if check_logged_in(sesh, 0):
        if delete_song_from_db(music_id):
            flash("Deleted successfully")
        else:
            flash("Could not delete song")
        return redirect("/admin")
    flash(
        "You are not allowed to access that page. Try logging in with a different account"
    )
    return redirect("/logout")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if check_logged_in(sesh, 0):
        num_songs = len(get_available_songs())
        num_listeners = get_number_of_listeners()
        num_creators = get_number_of_creators()
        num_playlists = len(get_available_playlists(sesh["username"]))
        return render_template(
            "admin.html",
            available_songs=get_available_songs(),
            num_songs=num_songs,
            num_listeners=num_listeners,
            num_creators=num_creators,
            num_playlists=num_playlists,
        )
    flash(
        "You are not allowed to access that page. Try logging in with a different account"
    )
    return redirect("/logout")


@app.route("/profile", methods=["GET"])
def profile():
    if check_logged_in(sesh, 1):
        return render_template("profile.html")
    flash(
        "You are not allowed to access that page. Try logging in with a different account"
    )
    return redirect("/logout")


@app.route("/search", methods=["POST"])
@app.route("/search?q=<query>", methods=["GET"])
def search(query: str):
    check_logged_in(sesh)
    if r.method == "POST":
        return jsonify(
            list(
                map(
                    lambda x: x.to_json(),
                    filter(
                        lambda song: song.search(r.form["query"]), get_available_songs()
                    ),
                )
            )
        )
    return render_template(
        "player.html",
        results=filter(lambda song: song.search(query), get_available_songs()),
    )


def check_logged_in(sesh: dict, user_type: int | None = None) -> bool:
    """Check whether a user is logged in.
    user_type 0 for admin, 1 for user, 2 for creator. Ignore user_type if you just want to check if they are logged in
    """
    if user_type == None and "username" in sesh:
        # Just checking if logged in as any user
        return True
    if ("user_type" not in sesh) or (sesh["user_type"] != user_type):
        # Checking if logged in as a specific user type
        return False
    return True


if __name__ == "__main__":
    load_dotenv()

    port = int(getenv("PORT")) if getenv("PORT") else 8000
    debug = str(getenv("DEBUG")).casefold() in {
        "y",
        "yes",
        "true",
    }

    app.run(host="0.0.0.0", port=port, debug=debug)
