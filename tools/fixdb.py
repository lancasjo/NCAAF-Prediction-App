from bs4 import BeautifulSoup
import requests
import re
import math
import string
import hashlib
import sys
sys.path.append('../')
#import backend.functions as functions


from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Connect to the database
uri = "mongodb+srv://jrlancaste:bugbugbug@sportsbetting.vqijjoh.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("Could not connect to database")
    sys.exit()

db = client["game-database"]
collection = db["weeks-collection"]
weeks = collection.find({})
def update_predictions():
    week_list = list(weeks)
    for i in range (8):
        games = week_list[i]["Games"]
        for game in games:
            game["Prediction"] -= 3
        print(games)
        collection.update_one({"Num": i}, {"$set": {"Games": games}})

    
def find_name_errors(weeks: dict) -> dict:
    week_counter = 0
    corrections = {}
    for week in weeks:
        week_counter += 1
        for game in week["Games"]:
            wrong = False
            if game["Home"] != functions.stdname(game["Home"]):
                if game["Home"] not in corrections:
                    corrections[game["Home"]] = functions.stdname(game["Home"])
            if game["Away"] != functions.stdname(game["Away"]):
                if game["Away"] not in corrections:
                    corrections[game["Away"]] = functions.stdname(game["Away"])
    return corrections

def fix_name_errors(corrections: dict, weeks: dict) -> dict:
    week_counter = 0
    for week in weeks:
        week_counter += 1
        for game in week["Games"]:
            wrong = False
            oldhome = str(game["Home"])
            oldaway = str(game["Away"])
            try:
                game["Home"] = corrections[game["Home"]]
                wrong = True
            except:
                pass
            try:
                game["Away"] = corrections[game["Away"]]
                wrong = True
            except:
                pass
            if wrong:
                old_id = game["_id"]
                game["_id"] = functions._generate_game_id(week_counter, game["Home"], game["Away"])
                print("Updated game " + str(old_id) + " to " + str(game["_id"]) + " in week " + str(week_counter))
                if oldhome != game["Home"]:
                    print("\tHome: " + oldhome + " -> " + game["Home"])
                if oldaway != game["Away"]:
                    print("\tAway: " + oldaway + " -> " + game["Away"])
        collection.update_one({"_id": week["_id"]}, {"$set": week}, upsert=False)

        