import hug
import sqlite3
import sqlite_utils
from sqlite_utils import Database
import requests
import os

db = Database(sqlite3.connect("./var/users.db"))

@hug.get("/users/")
def users():
    return {"users": db["users"].rows}

@hug.get("/users/{username}")
def retrieveUser(response, username: hug.types.text):
    user = {}
    try:
        user = db["users"].get(username)
    except sqlite_utils.db.NotFoundError:
        response.status = hug.falcon.HTTP_404
    return {"user": user}

@hug.post("/users/", status=hug.falcon.HTTP_201)
def createUser(
    response,
    username: hug.types.text,
    bio: hug.types.text,
    email: hug.types.text,
    password: hug.types.text,
):
    newUser = {
        "username": username,
        "bio": bio,
        "email": email,
        "password": password,
    }

    try:
        db["users"].insert(newUser)
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}

    response.set_header("Location", f"/users/{newUser['username']}")
    return newUser

@hug.get("/users/{username}/followers")
def retrieveFollowers(response, username: hug.types.text):
    followers = {}
    try:
        followers = db["followers"].rows_where("username = ?", [username])
    except sqlite_utils.db.NotFoundError:
        response.status = hug.falcon.HTTP_404
    return {"followers": followers}

@hug.post("/users/{username}/followers", status=hug.falcon.HTTP_201)
def createFollower(response, username: hug.types.text, followername: hug.types.text):
    newFollower = { "id": db["followers"].last_pk, "username": username, "followername": followername }

    #if the follower is not an existing user, throw an error
    try:
        db["users"].get(followername)
    except sqlite_utils.db.NotFoundError:
        response.status = hug.falcon.HTTP_409
        return {"error": "follower does not exist"}

    try:
        db["followers"].insert(newFollower)
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}

    response.set_header("Location", f"/following/{newFollower['id']}")
    return newFollower

@hug.get("/users/health")
def healthCheck(response):
    return {"health" : "good"}

@hug.startup()
def register(url: hug.types.text):
    port = os.environ["PORT"]
    url = f"http://localhost:{port}/users"
    requests.post("http://localhost:8400/register", data={"url": url, "name": "users"})
