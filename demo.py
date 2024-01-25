from random import randint
from faker import Faker
from src.database import db

for i in range(100):
    name = Faker().name()
    _id = randint(0, 1)
    username = Faker().email()
    if not db.exists("users", (username,)):
        db.insert(
            "users",
            username,
            name,
            _id,
        )
    print(db.fetchone("users", (username,)))
