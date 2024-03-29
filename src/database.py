from json import load
from os import remove
from os.path import dirname, splitext
from sqlite3 import connect

from .miscellaneous import hasher

primary_keys = {
    "users": "username",
    "music": "music_id",
    "playlists": "playlist_id",
    "blacklist": "text",
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

    def like(self, table: str, key: str) -> bool:
        cur = self.db.cursor()
        res = cur.execute(
            f"SELECT * FROM {table} WHERE {primary_keys[table]} LIKE '%{str(key).casefold()}%'",
        )
        data = res.fetchall()
        cur.close()
        return bool(data)

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


def add_to_blacklist(text: str) -> bool:
    return db.insert_if_not_exists("blacklist", text)


class Song:
    def __init__(self, db_row: list):
        self.music_id = db_row[0]
        self.name = db_row[1]
        self.artist = db_row[2]
        self.album = db_row[3]
        self.genre = db_row[4]
        self.year = db_row[5]
        self.lyrics = db_row[6]
        self.owner = db_row[7]
        self.search_data = [
            self.music_id.casefold(),
            self.name.casefold(),
            self.artist.casefold(),
            self.album.casefold(),
            self.genre.casefold(),
            str(self.year),
        ]

    def search(self, query: str) -> bool:
        q = query.casefold().strip()
        for data in self.search_data:
            if q in data:
                return True
        return False

    def to_json(self) -> dict:
        return self.__dict__

    def __str__(self) -> str:
        return self.__dict__.__str__()

    def __repr__(self) -> str:
        return self.__str__()


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


def add_song_to_db(song: Song, music_file) -> bool:
    # Add to database and save mp4 into the static/audio folder, with the music_id.mp4 as the file name
    # Also check if it exists in blacklist

    if db.like("blacklist", song.name) or db.like("blacklist", song.artist):
        return False
    music_file.save(dirname(__file__) + f"/../static/audio/{song.music_id}")
    print(f"Saved file {song.music_id}")
    return db.insert_if_not_exists(
        "music",
        song.music_id,
        song.name,
        song.artist,
        song.album,
        song.genre,
        song.year,
        song.lyrics,
        song.owner,
    )


def delete_song_from_db(music_id: str) -> bool:
    # Delete song from the database and from the static/audio folder
    try:
        if db.exists("music", music_id):
            remove(dirname(__file__) + f"/../static/audio/{music_id}")
            db.execute("DELETE FROM music WHERE music_id=?", (music_id,))
            return True
    except Exception as e:
        print(e)
    return False


def get_available_songs() -> list[Song]:
    return list(map(lambda x: Song(x), db.fetchall("music")))


def get_available_playlists(username: str) -> list[Playlist]:
    '''
    Fetch all playlists that have a privacy of 0 or if have been created by the user
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
    # Check if admin, user_type 0
    if fetch_user_details(username)[3] == 0:
        return list(map(lambda x: Playlist(x), db.fetchall("playlists")))

    return list(
        map(
            lambda x: Playlist(x),
            filter(
                lambda x: x[4] == 0 or x[2] == username,
                db.fetchall("playlists"),
            ),
        )
    )


def fetch_song_details_from_db(music_id: str) -> Song:
    # Fetch song details from the db and return it as a Song object
    return Song(db.fetchone("music", (music_id,)))


def update_song_details_in_db(music_id: str, *params) -> bool:
    # Update song details in the db
    db.execute(
        "UPDATE music SET name=?, artist=?, album=?, genre=?, year=?, lyrics=? WHERE music_id=?",
        params + (music_id,),
    )
    return True


def get_number_of_listeners() -> int:
    return len(list(filter(lambda x: x[3] == 1, db.fetchall("users"))))


def get_number_of_creators() -> int:
    return len(list(filter(lambda x: x[3] == 2, db.fetchall("users"))))


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
            year INT NOT NULL,
            lyrics VARCHAR(1000) NOT NULL,
            owner VARCHAR(20) NOT NULL,
            FOREIGN KEY (owner) REFERENCES users(username)
            )
        """
    )

    db.execute(
        f"""CREATE TABLE IF NOT EXISTS playlists
               (
                    playlist_id VARCHAR(20) PRIMARY KEY NOT NULL,
                    name VARCHAR(20) NOT NULL,
                    owner VARCHAR(20) NOT NULL,
                    music_ids VARCHAR(20) NOT NULL,-- Comma separated list of music_ids
                    privacy INT NOT NULL DEFAULT 0,
                    FOREIGN KEY (owner) REFERENCES users(username)
               )
    """
    )

    db.execute(
        f"""CREATE TABLE IF NOT EXISTS blacklist
        (
            text VARCHAR(20) PRIMARY KEY NOT NULL
        )
        """
    )

    create_user("admin", "admin", "Admin", 0)  # Admin
    create_user("user", "user", "Vishal N", 1)  # Normal user
    create_user("creator", "creator", "Arijit Singh", 2)  # Creator user

    with open("data.json", "r") as f:
        data = load(f)
        for song in data:
            db.insert_if_not_exists(
                "music",
                song["music_id"],
                song["name"],
                song["artist"],
                song["album"],
                song["genre"],
                song["year"],
                song["lyrics"],
                song["added_by"],
            )

    # print(db.fetchall("users"))
    # print(db.fetchall("music"))
