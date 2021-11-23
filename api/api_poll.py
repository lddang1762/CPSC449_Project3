import hug
import boto3
import random
from boto3.dynamodb.conditions import Key
from datetime import datetime
import requests
import os

session = boto3.Session(
    aws_access_key_id = 'fakeMyKeyId',
    aws_secret_access_key = 'fakeSecretAccessKey'
)

dynamodb = session.resource('dynamodb', endpoint_url='http://localhost:9000')

@hug.post("/polls/create")
def createPoll(
    response,
    username: hug.types.text,
    question: hug.types.text,
    responses: hug.types.multiple
):
    if len(responses) > 4:
        return {"error": "Too many responses"}

    table = dynamodb.Table("Polls")
    try:
        # enerate random id
        startDate = int(datetime.now().strftime("%m%d%y%H%M%S"))
        pollId = random.randrange(0, startDate)
        print(pollId)

        createdPoll = {
            "pollId": pollId,
            "creator": username,
            "question": question,
            "responses": responses,
        }

        table.put_item(
            Item={
                "pollId": pollId,
                "startDate": startDate,
                "creator": username,
                "question": question,
                "responses": responses,
                "responseCount0": 0,
                "responseCount1": 0,
                "responseCount2": 0,
                "responseCount3": 0,
                "voteCount": 0,
                "voters": [],
            }
        )
        pollId += 1
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}
    return createdPoll

@hug.post("/polls/{pollId}/vote")
def pollVote(
    response,
    username: hug.types.text,
    pollId: hug.types.number,
    choice: hug.types.number):

    responses = {
        0: "responseCount0",
        1: "responseCount1",
        2: "responseCount2",
        3: "responseCount3",
    }

    voteChoice = responses.get(choice)
    print(voteChoice)

    table = dynamodb.Table("Polls")
    try:
        poll = table.query(
            KeyConditionExpression=Key("pollId").eq(pollId)
        )
        startDate = poll["Items"][0]["startDate"]
        table.update_item(
            Key={"pollId": pollId, "startDate": startDate},
            UpdateExpression="SET voteCount = voteCount + :inc, voters = list_append(voters, :username), #CHOICE = #CHOICE + :inc",
            ConditionExpression="not contains (voters, :userStr)", # prevent voting again
            ExpressionAttributeNames={
                "#CHOICE": voteChoice
            },
            ExpressionAttributeValues={
                ":inc": 1,
                ":username": [username],
                ":userStr": username,
            },
            ReturnValues="UPDATED_NEW"
        )
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}
    return {f"{username} successfully voted on poll {pollId} with response {choice}"}

@hug.get("/polls/{pollId}")
def retrievePoll(response, pollId: hug.types.number):
    table = dynamodb.Table("Polls")
    poll = {}
    try:
        poll = table.query(
            KeyConditionExpression=Key("pollId").eq(pollId)
        )
    except Exception as e:
        response.status = hug.falcon.HTTP_409
        return {"error": str(e)}
    return {"poll": poll["Items"][0]}

@hug.get("/polls/health")
def healthCheck(response):
    return {"health" : "good"}

@hug.startup()
def register(url: hug.types.text):
    port = os.environ["PORT"]
    url = f"http://localhost:{port}/polls"
    requests.post("http://localhost:8400/register", data={"url": url, "name": "polls"})
