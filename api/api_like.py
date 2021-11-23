import hug
import redis
import sqlite3
import sqlite_utils
from sqlite_utils import Database
import requests
import os

db = Database(sqlite3.connect('./var/posts.db'))

r = redis.Redis()
key = 0

@hug.post("/posts/{postId}/likes")
def like(response, username: hug.types.text, postId: hug.types.number):
    likedPost = { "username": username, "postId": postId }
    global key
    try:
        r.hmset(key, likedPost)
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}

    key += 1
    return likedPost

@hug.get("/posts/{postId}/likes")
def retrievePostLikes(response, postId: hug.types.number):
    numLikes = 0
    try:
        for x in range(key):
            likedPosts = r.hgetall(x)
            postLikes = { key.decode(): value.decode() for key, value in likedPosts.items() }
            if int(postLikes["postId"]) == postId:
                numLikes += 1
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}

    return {"postLikeCount": numLikes}

@hug.get("/users/{username}/likes/")
def retrieveUserLikes(response, username: hug.types.text):
    posts = []
    try:
        for x in range(key):
            # get object mapped at key
            likedPosts = r.hgetall(x)
            userLikes = { key.decode(): value.decode() for key, value in likedPosts.items() }
            if userLikes["username"] == username:
                posts.append({"postId": userLikes["postId"]})
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}

    return {"userLikes": posts}

@hug.get("/posts/popular")
def retrievePopularPosts(response):
    likeThreshold = 2
    posts = []
    try:
        # create set so all postIDs are unique
        postIds = set()
        for x in range(key):
            # get object mapped at key
            likedPosts = r.hgetall(x)
            likedPosts = { key.decode(): value.decode() for key, value in likedPosts.items() }
            postIds.add(int(likedPosts["postId"]))
        # for each postID, get like count and add if past threshold
        for postId in postIds:
            likes = retrievePostLikes(response, postId)
            # if post exceeds threshold, get from database
            if(int(likes["postLikeCount"]) >= likeThreshold):
                popularPost = db["posts"].get(postId)
                posts.append(popularPost)


    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}

    return {"popularPosts": posts}

@hug.get("/likes/health")
def healthCheck(response):
    return {"health" : "good"}

@hug.startup()
def register(url: hug.types.text):
    port = os.environ["PORT"]
    url = f"http://localhost:{port}/likes"
    requests.post("http://localhost:8400/register", data={"url": url, "name": "likes"})


def populate():
    global key
    global r
    r.hmset(key, {"username": "Arkadbe", "postId": 1})
    key += 1
    r.hmset(key, {"username": "Arkadbe", "postId": 2})
    key += 1
    r.hmset(key, {"username": "Buggyna", "postId": 0})
    key += 1
    r.hmset(key, {"username": "Buggyna", "postId": 2})
    key += 1
    r.hmset(key, {"username": "Champob", "postId": 1})
    key += 1
    r.hmset(key, {"username": "Champob", "postId": 2})
    key += 1
    r.hmset(key, {"username": "Dancent", "postId": 1})
    key += 1
    r.hmset(key, {"username": "Dancent", "postId": 2})
    key += 1
    r.hmset(key, {"username": "Dancent", "postId": 4})
    key += 1

populate()
