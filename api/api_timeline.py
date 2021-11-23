import hug
import json
import requests
import datetime
import sqlite3
import sqlite_utils
from sqlite_utils import Database
import requests
import os

db = Database(sqlite3.connect('./var/posts.db'))

def authenticate(username, password):
    req = requests.get(f"http://localhost:8000/users/{username}")
    data = json.loads(req.text)
    user = data["user"]
    if user["password"] == password:
        return user
    return False

@hug.get("/")
def publicTimeline():
    return {"posts": db["posts"].rows_where(order_by = "timestamp desc")}

@hug.get("/timeline/{username}")
def userTimeline(response, username: hug.types.text):
    posts = []
    try:
        posts = db["posts"].rows_where("username = ?", [username], order_by = "timestamp desc")
    except sqlite_utils.db.NotFoundError:
        response.status = hug.falcon.HTTP_404

    return {"userPosts": posts}

@hug.get("/home", requires = hug.authentication.basic(authenticate))
def homeTimeline(response, user: hug.directives.user):
    posts = []
    username = user["username"]
    req = requests.get(f"http://localhost:8000/users/{username}/followers")
    data = json.loads(req.text)

    followers = []
    try:
        for rows in data["followers"]:
            followername = rows["followername"]
            for post in db["posts"].rows_where("username = ?", [followername]):
                posts.append(post)
            posts.sort(key=lambda post: post["timestamp"], reverse=True)
    except sqlite_utils.db.NotFoundError:
        response.status = hug.falcon.HTTP_404

    return {"latestPosts": posts}

@hug.get("/posts/{postId}")
def retrievePost(response, postId: hug.types.number):
    post = []
    try:
        post = db["posts"].get(postId)
        # # display repost url if repost
        # if post["repostId"] >= 0:
        #     repost = db["posts"].get(post["repostId"])
        #     repostId = repost["id"]
        #     post["repostId"] = f"http://localhost:8100/posts/{repostId}"
    except sqlite_utils.db.NotFoundError:
        response.status = hug.falcon.HTTP_404
    return {"post": post}

@hug.post("/posts/", requires = hug.authentication.basic(authenticate), status = hug.falcon.HTTP_201)
def createPost(
    response,
    user: hug.directives.user,
    text: hug.types.text,
):
    post = {
        "id": db["posts"].last_pk,
        "username": user["username"],
        "text": text,
        "timestamp": datetime.datetime.now(),
        "repostId": -1
    }

    # check if repost,
    username = user["username"]
    print(username)
    try:
        repost = db["posts"].rows_where("username = ? AND text = ?", [username,text])
        repost = (list(repost)[0])
        repostId = repost["id"]
        post["repostId"] = f"http://localhost:8100/posts/{repostId}"
    except sqlite_utils.db.NotFoundError:
        print("not a repost")

    try:
        db["posts"].insert(post)
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}

    id = post["id"]
    response.set_header("Location", f"/posts/{id}")
    return post

@hug.get("/timeline/health")
def healthCheck(response):
    return {"health" : "good"}

@hug.startup()
def register(url: hug.types.text):
    port = os.environ["PORT"]
    url = f"http://localhost:{port}/timeline"
    requests.post("http://localhost:8400/register", data={"url": url, "name": "timeline"})
