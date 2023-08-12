from bs4 import BeautifulSoup
import requests
import re
import math
import string

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class Game:
    def __init__(self, home : str, away : str, spread : float, prediction : float, success : bool, home_score : int, away_score : int):
        self.Home = home
        self.Away = away
        self.Spread = spread
        self.Prediction = prediction
        self.Success = success
        self.HomeScore = home_score
        self.AwayScore = away_score
    
    def turn_to_dict(self):
        
        return {
            "Away": self.Away,
            "Home": self.Home,
            "Spread": self.Spread,
            "Prediction": self.Prediction,
            "Success": self.Success,
            "Home Score": self.HomeScore,
            "Away Score": self.AwayScore
        }

class Week:
    def __init__(self, num : int, games : list, correct : int, incorrect : int, num_games : int):
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

uri = "mongodb+srv://jrlancaste:bugbugbug@sportsbetting.vqijjoh.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

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

def run(): 
    
    response = requests.get("http://sagarin.com/sports/cfsend.htm")
    soup = BeautifulSoup(response.content, "html.parser")
    pre_tags = soup.find_all("pre")
    html_content = pre_tags[2].get_text()
    teams = html_content.splitlines()
    find_scores(teams)

    response = requests.get("https://www.vegasinsider.com/college-football/odds/las-vegas/")
    soup = BeautifulSoup(response.content, "html.parser")
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


    #print("Suggessted bets:")
    total = 0
    for game in data:
        if game[1] > 4:
            total += 1
            #print("\nTake " + game[0][0] + " at " + game[0][1] + " (Predicted line " + str(game[2]) + ")")
        elif game[1] < -4:
            total += 1
            #print("\nTake " + game[0][1] + " against " + game[0][0] + " (Predicted line " + str(game[2]) + ")")

    win = total * 110.0/210.0
    win = math.ceil(win)
    #print("\nYou must win " + str(win) + " out of " + str(total) + " to profit")
    return data

#Create list of games to add to week
#Trying to make a function that needs to be ran once per week, on monday
#data is a list all of the necessary data, before the game is played
#data does not contain the game score
def run_on_mondays():
    data = run()
    weekly_game_prediction_list = []
    for game in data:
        #check if prediction is far enough from spread to be considered a good bet
        if game[1] > 4 or game[1] < -4:
            weekly_game_prediction_list.append(Game(game[0][1], game[0][0], game[3], game[2], False, -1, -1))
    
    week_number = 1 # scrape from vegas insider
    #Delete this weeks document to avoid duplicate
    qeury = {"Num", week_number}
    gameDB = client["game-database"] #database name
    weeks = gameDB["weeks-collection"] #collection name
    week = Week(week_number, weekly_game_prediction_list, 0, 0, len(weekly_game_prediction_list))

    weeks.delete_one(qeury)
    weeks.insert_one(week.turn_to_dict())

run_on_mondays()
client.close()


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

def writeToDB():
    return




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
