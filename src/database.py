from sqlite3 import connect

from .miscellaneous import hasher

primary_keys = {
    "users": "username",
    "music": "music_id",
    "playlists": "playlist_id",
    "blacklist": "name",
}


class SqliteWrapper:
    def __init__(self, path):
        self.db = connect(path, check_same_thread=False)

    def execute(self, query, *params):
        cur = self.db.cursor()
        cur.execute(query, *params)
        self.db.commit()

    def insert(self, table, *params):
        self.execute(
            f"INSERT INTO {table} VALUES ({('?,'*len(*params)).strip(", ")})", *params
        )

    def fetchone(self, table, *params):
        cur = self.db.cursor()
        res = cur.execute(
            f"SELECT * FROM {table} WHERE {primary_keys[table]}=?", *params
        )
        data = res.fetchone()
        cur.close()
        return data

    def fetchall(self, table):
        cur = self.db.cursor()
        res = cur.execute(f"SELECT * FROM {table}")
        data = res.fetchall()
        cur.close()
        return data

    def exists(self, table, key) -> bool:
        return self.fetchone(table, (key,)) != None

    def insert_if_not_exists(self, table, key, *params):
        if not self.exists(table, key):
            self.insert(table, (key,) + params)
            return True
        return False


def check_user_exists(username: str) -> bool:
    return bool(db.fetchone("users", (username,)))


def fetch_user_details(username: str) -> list:
    row = db.fetchone("users", (username,))
    return row if row else []


def check_password(username: str, entered_password: str) -> bool:
    row = db.fetchone("users", (username,))
    return hasher(entered_password) == row[1] if row else False


def create_user(username: str, password: str, name: str, type: int) -> bool:
    return db.insert_if_not_exists("users", username, hasher(password), name, type)


class Song:
    def __init__(self, db_row: list):
        self.music_id = db_row[0]
        self.name = db_row[1]
        self.artist = db_row[2]
        self.album = db_row[3]
        self.genre = db_row[4]
        self.year = db_row[5]


class Playlist:
    def __init__(self, db_row: list):
        self.playlist_id = db_row[0]
        self.name = db_row[1]
        self.owner = db_row[2]
        self.music_ids = db_row[3].split(",")
        self.privacy = db_row[4]
        self.music = list(
            map(lambda x: Song(db.fetchone("music", (x,))), self.music_ids)
        )


def get_available_songs() -> list[Song]:
    return list(map(lambda x: Song(x), db.fetchall("music")))


def get_available_playlists(username: str) -> list[Playlist]:
    '''
    ""CREATE TABLE IF NOT EXISTS playlists
               (
                    playlist_id VARCHAR(20) PRIMARY KEY NOT NULL,
                    name VARCHAR(20) NOT NULL,
                    owner VARCHAR(20) NOT NULL,
                    music_ids VARCHAR(20) NOT NULL,
                    privacy INT NOT NULL DEFAULT 0,
                    FOREIGN KEY (owner) REFERENCES users(username)
               )
    """
    '''
    # Fetch all playlists that have a privacy of 0 or if have been created by the user
    return list(
        map(
            lambda x: Playlist(x),
            filter(
                lambda x: x[4] == 0 or x[2] == username,
                db.fetchall("playlists"),
            ),
        )
    )


if __name__ in {"database", "src.database", "__main__"}:
    db = SqliteWrapper("music-app.db")

    # user_type 0 = admin; 1 = user; 2 = creator
    db.execute(
        """CREATE TABLE IF NOT EXISTS users
            (
                username VARCHAR(20) PRIMARY KEY NOT NULL,
                password VARCHAR(64) NOT NULL,
                name VARCHAR(20) NOT NULL,
                user_type INT NOT NULL
            )
        """
    )

    db.execute(
        """CREATE TABLE IF NOT EXISTS music
            (
            music_id VARCHAR(20) PRIMARY KEY NOT NULL,
            name VARCHAR(20) NOT NULL,
            artist VARCHAR(20) NOT NULL,
            album VARCHAR(20) NOT NULL,
            genre VARCHAR(20) NOT NULL,
            year INT NOT NULL
            )
        """
    )

    db.execute(
        f"""CREATE TABLE IF NOT EXISTS playlists
               (
                    playlist_id VARCHAR(20) PRIMARY KEY NOT NULL,
                    name VARCHAR(20) NOT NULL,
                    owner VARCHAR(20) NOT NULL,
                    music_ids VARCHAR(20) NOT NULL,
                    privacy INT NOT NULL DEFAULT 0,
                    FOREIGN KEY (owner) REFERENCES users(username)
               )
    """
    )

    db.execute(
        """CREATE TABLE IF NOT EXISTS blacklist
        (
            artist VARCHAR(20),
            album VARCHAR(20),
            name VARCHAR(20)
        )
        """
    )

    create_user("user", "user", "Vishal N", 1)  # Normal user
    create_user("creator", "creator", "Arijit Singh", 1)  # Normal user
    create_user("admin", "admin", "Admin", 0)  # Admin

    # Read a json file at data.json and insert all the songs into the database
    """JSON file is a list of dictionaries, with each dictionary in he format     {
        "music_id": "blankspace",
        "name": "Blank Space",
        "artist": "Taylor Swift",
        "album": "1989",
        "genre": "Pop",
        "year": "2014"
    },"""
    import json

    with open("data.json", "r") as f:
        data = json.load(f)
        for song in data:
            db.insert_if_not_exists(
                "music",
                song["music_id"],
                song["name"],
                song["artist"],
                song["album"],
                song["genre"],
                song["year"],
            )

    print(db.fetchall("users"))
    print(db.fetchall("music"))

else:
    print(__name__)
