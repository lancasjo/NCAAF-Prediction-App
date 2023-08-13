from bs4 import BeautifulSoup
import requests
import re
import math
import string
import hashlib
import sys

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class Game:
    def __init__(self, week: int, home : str, away : str, spread : float, prediction : float, success : bool, home_score : int, away_score : int):
        self.Week = week
        self.Home = home
        self.Away = away
        self.Spread = spread
        self.Prediction = prediction
        self.Success = success
        self.HomeScore = home_score
        self.AwayScore = away_score
        self._id = generate_game_id(self)
    
    def update(self, new_game):
        self.Spread = new_game.Spread
        self.Prediction = new_game.Prediction
        self.Success = new_game.Success
        self.HomeScore = new_game.HomeScore
        self.AwayScore = new_game.AwayScore

    
    def turn_to_dict(self):
        
        return {
            "_id": self._id,
            "Away": self.Away,
            "Home": self.Home,
            "Spread": self.Spread,
            "Prediction": self.Prediction,
            "Success": self.Success,
            "Home Score": self.HomeScore,
            "Away Score": self.AwayScore
        }

class Week:
    def __init__(self, num : int, games : list, correct : int , incorrect : int , num_games : int):
        self.Num = num
        self.Games = games
        self.Correct = 0
        self.Incorrect = 0
        self.NumGames = num_games
        
    def turn_to_dict(self):
        return {
            "Num": self.Num,
            "Games": [game.turn_to_dict() for game in self.Games],
            "Correct": self.Correct,
            "Incorrect": self.Incorrect,
            "Num Games": self.NumGames
        }
    
    def update(self):
        self.NumGames = len(self.Games)
        for game in self.Games:
            if game.Success:
                self.Correct += 1
            else:
                self.Incorrect += 1
        
    
name_conversion = {"UMass": "Massachusetts",
                    "USC": "Southern California",
                    "Florida International": "Fla International",
                    "UConn": "Connecticut",
                    "Miami (OH)": "MiamiOhio",
                    "Miami": "MiamiFlorida",
                    "Texas A&M": "Texas AM",
                    "Army": "Army West Point",
                    "UL Monroe": "LouisianaMonroeULM",
                    "UCF": "Central FloridaUCF",
                    "St. Francis (PA)": "Saint FrancisPa",
                    "North Carolina A&T": "NC AT"}

#uri = "mongodb+srv://jrlancaste:bugbugbug@sportsbetting.vqijjoh.mongodb.net/?retryWrites=true&w=majority"

#URI for local testing 
uri = "mongodb://localhost:27017/?readPreference=primary&ssl=false&retryWrites=true&w=majority&appname=NCAAFBetting"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("Could not connect to database")
    sys.exit()




def convert_signed_string_to_number(signed_string : str):
    signed_string = signed_string.strip()  # Remove leading and trailing spaces
    sign = 1 if signed_string[0] == "+" else -1
    number = float(signed_string[1:])
    return sign * number

team_scores = {}


def extract_state_and_number(line : str):
    translator = str.maketrans("", "", string.punctuation)

    modified_string = line.translate(translator)

    #pattern = r'^\s*(\d+)\s+([A-Za-z\s]+)\s+=\s+(\d+\.\d+)\s+'
    pattern = r'^\s*\d+\s+([A-Za-z\s]+)\s+[A-Z]+\s+(\d+)\s+'

    match = re.match(pattern, modified_string)
    
    if match:
        team = match.group(1).strip()
        score = int(match.group(2))
        team_scores[team] = score
    
        
def find_scores(list : list):
    for line in list:
        extract_state_and_number(line)
        
def find_odds(tbody_tag):
    game_odds = {}

    tr_tags = tbody_tag.find_all("tr", class_=["divided", "footer"])
    i = 0
    while i < len(tr_tags)-1:
        content = tr_tags[i].find(class_="team-name")
        away_team = content.find("span").get_text()
        i += 1
        content = tr_tags[i].find(class_="team-name")
        home_team = content.find("span").get_text()
        pair = (away_team.strip(), home_team.strip())
        
        td_tags = tr_tags[i].find_all("td", class_="game-odds")
        
        fanduel = td_tags[1].find("span", class_="data-value").get_text()
        betMGM = td_tags[2].find("span", class_="data-value").get_text()
        draftKings = td_tags[6].find("span", class_="data-value").get_text()
        odds = [fanduel]
        spreads = []
        skip = False
        for j in range(0, len(odds)):
            if "N/A" in odds[j]:
                skip = True
                break
            if "PK" in odds[j]:
                spread = 0
            else:
                spread = convert_signed_string_to_number(odds[j])
                spreads.append(spread)
        if not skip:
            game_odds[pair] = spreads
        i += 1
    
    return game_odds


def _generate_game_id(week : int, home : str, away : str):
    combined_data = f"{week}{home}{away}"
    hash_object = hashlib.md5(combined_data.encode())
    return hash_object.hexdigest()

def generate_game_id(game : Game):
    return _generate_game_id(game.Week, game.Home, game.Away)

def update_week(week : dict) -> dict:
    week["Num Games"] = len(week["Games"])
    for game in week["Games"]:
        if game["Success"]:
            week["Correct"] += 1
        else:
            week["Incorrect"] += 1
    return week

def scrape_sagrin():
    response = requests.get("http://sagarin.com/sports/cfsend.htm")
    soup = BeautifulSoup(response.content, "html.parser")
    
    return soup
def scrape_vegas_insider():
    response = requests.get("https://www.vegasinsider.com/college-football/odds/las-vegas/")
    soup = BeautifulSoup(response.content, "html.parser")
    return soup

def check_html_updates():
    soup = scrape_sagrin()
    pre_tags = soup.find_all("pre")
    sagrin_content = pre_tags[2].get_text()
    
    soup = scrape_vegas_insider()
    vegas_content = soup.find("tbody", id="odds-table-spread--0").get_text()
    
    db = client["game-database"]
    collection = db["html_content"]
    
    old_sagrin = collection.find({"sagrin": sagrin_content})
    old_vegas = collection.find({"vegas": vegas_content})
    return old_sagrin and old_vegas
    
    
def run() -> list: 
    soup = scrape_sagrin()
    pre_tags = soup.find_all("pre")
    html_content = pre_tags[2].get_text()
    teams = html_content.splitlines()
    find_scores(teams)

    soup = scrape_vegas_insider()
    tbody_tag = soup.find("tbody", id="odds-table-spread--0")
    game_odds = find_odds(tbody_tag) 

    data = []

    for teams, spreads in game_odds.items():
        away = teams[0]
        home = teams[1]
        if away not in team_scores:
            away = name_conversion[away]
        if home not in team_scores:
            home = name_conversion[home]
        prediction = team_scores[away] - team_scores[home] - 500
        
        
        diff = prediction/100.0 - spreads[0]
        diff = round(diff, 2)
        data.append((teams, diff, prediction/100.0, spreads[0]))


    total = 0
    for game in data:
        if game[1] > 4:
            total += 1
        elif game[1] < -4:
            total += 1

    win = total * 110.0/210.0
    win = math.ceil(win)
    return data


def update_bets():
    new_data = run()
    prev_data = []
    #get current data from db if it exists
    #if it doesn't exist, create a new week
    #if it does exist, re-evaluate the week against the new data and update the db

    #get current week from db
    gameDB = client["game-database"] #database name
    weeks = gameDB["weeks-collection"] #collection name
    query = {"Num": 1}
    week = weeks.find_one(query)
    if week == None:
        prev_data = False
    else:
        prev_data = True
    games_to_add = []
    
    week_number = 1 # scrape from vegas insider

    for game in new_data:
        #check if prediction is far enough from spread to be considered a good bet
        if game[1] > 4 or game[1] < -4:
            games_to_add.append(Game(week_number, game[0][1], game[0][0], game[3], game[2], False, -1, -1))
    
    games_to_add.sort(key=lambda x: x.Home)

    #add games to week
    if prev_data:
        for new_game in games_to_add:
            existing_game = next((game for game in week["Games"] if game["_id"] == new_game._id), None)
            if existing_game:
                existing_game = new_game.turn_to_dict()
            else:
                week["Games"].append(new_game.turn_to_dict())
        week = update_week(week)
        weeks.update_one(query, {"$set": week}, upsert=True)

    else:
        new_week = Week(week_number, games_to_add, 0, 0, len(games_to_add))
        new_week.update()
        weeks.insert_one(new_week.turn_to_dict())

    print("Week " + str(week_number) + " added to database")


def update_html():
    soup = scrape_sagrin()
    pre_tags = soup.find_all("pre")
    sagrin_content = pre_tags[2].get_text()
    
    soup = scrape_vegas_insider()
    vegas_content = soup.find("tbody", id="odds-table-spread--0").get_text()

    db = client["game-database"]
    collection = db["html_content"]
    collection.insert_one({"sagrin": sagrin_content, "vegas": vegas_content})
    print("HTML updated")


def update_db():
    update_html()
    update_bets()
    print("Database updated")




#example of adding to database   
# gameDB = client["game-database"] #database name
# weeks = gameDB["weeks-collection"] #collection name
# gameExample = { #data
#     "home": "michigan",
#     "away": "OSU",
#     "homeScore": 100,
#     "awayScore": 0
# }
# example_game = Game("michigan", "OSU", -10, -50, True, 100, 0)
# game_dict = example_game.turn_to_dict()
# weeks.insert_one(game_dict) #add data to collection

def onChange():
    print("There was a change!!")




### END FUNCTION DEFINITIONS ###
#Database schema
# {
#    Week : int
#    {
#      [ Game : 
#        {
#           Home : string
#           Away : string
#           Spread : float
#           Prediction : float
#           Success : bool
#           HomeScore : int
#           AwayScore : int
#        }
#      ]
#      Correct : int
#      Incorrect : int
#      NumGames : int
#    }
# }
# Is there a double counting issue here? NO!!
# There is a world where each team has a unique id in a seperate collection and relationships are established that way. Not that I see
# This way someone could look up a team and see all of their games instead of by week. Second DB, or could be done efficiently with queries