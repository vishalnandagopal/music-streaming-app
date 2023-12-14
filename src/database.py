from sqlite3 import connect

from .miscellaneous import hasher

primary_keys = {"users": "username", "music": "music_id"}


class SqliteWrapper:
    def __init__(self, path):
        self.db = connect(path)

    def execute(self, query, *params):
        cur = self.db.cursor()
        cur.execute(query, *params)
        self.db.commit()
        cur.close()

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
    return bool(db.fetchone("users", username))


def fetch_user_details(username: str) -> list:
    row = db.fetchone("users", username)
    return row if row else []


def check_password(username: str, entered_password: str) -> bool:
    row = db.fetchone("users", username)
    return hasher(entered_password) == row[1] if row else False


def create_user(username: str, password: str, name: str, type: int) -> bool:
    return db.insert_if_not_exists("users", username, hasher(password), name, type)


if __name__ in {"database", "src.database", "__main__"}:
    db = SqliteWrapper("music-app.db")

    # user_type 0 = admin; 1 = user; 2 = creator
    db.execute(
        """CREATE TABLE IF NOT EXISTS users
            (
                username varchar(20) PRIMARY KEY NOT NULL,
                password varchar(64) NOT NULL,
                name varchar(20) NOT NULL,
                user_type int NOT NULL
            )
            """
    )

    db.execute(
        """CREATE TABLE IF NOT EXISTS music
            (
                music_id varchar(20) PRIMARY KEY NOT NULL,
                name varchar(20) NOT NULL,
                artist varchar(20) NOT NULL,
                genre varchar(10),
                album varchar(20),
                added_on DATE
            )
            """
    )

    create_user("vishal", "password", "Vishal N", 1)  # Normal user
    create_user("admin", "root", "Admin", 0)  # Admin
    print(db.fetchall("users"))
else:
    print(__name__)
