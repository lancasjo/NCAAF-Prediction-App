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
        
#convert all names to a standard format
name_conversion = { "UMass": "Massachusetts",
                    "USC": "Southern California",
                    "Fla International": "Florida International",
                    "FIU": "Florida International",
                    "UConn": "Connecticut",
                    "MiamiOhio" : "Miami (OH)",
                    "MiamiFlorida": "Miami (FL)",
                    "Miami": "Miami (FL)",
                    "Texas AM": "Texas A&M",
                    "Mississippi": "Ole Miss",
                    "Army": "Army West Point",
                    "LouisianaMonroeULM": "UL Monroe",
                    "UCF": "Central FloridaUCF",
                    "Saint FrancisPa": "St. Francis (PA)",
                    "NC AT" : "North Carolina A&T",
                    "Sam Houston": "Sam Houston State",
                    "NIU": "Northern Illinois",
                    "Southern Miss": "Southern Mississippi",
                    "Southern Miss.": "Southern Mississippi",
                    "App State": "Appalachian State",
                    }

#standardize all naming conventions to sagrin
def stdname(name : str) -> str:
    if "St." in name:
        name = name.replace("St.", "State")
    if "Mich." in name:
        name = name.replace("Mich.", "Michigan")
    if "Fla." in name:
        name = name.replace("Fla.", "Florida")
    if "Ky." in name:
        name = name.replace("Ky.", "Kentucky")
    if "Tenn." in name:
        name = name.replace("Tenn.", "Tennessee")
    if "Ga." in name:
        name = name.replace("Ga.", "Georgia")
    if name in name_conversion:
        name = name_conversion[name]
    return name



uri = "mongodb+srv://jrlancaste:bugbugbug@sportsbetting.vqijjoh.mongodb.net/?retryWrites=true&w=majority"

#URI for local testing 
#uri = "mongodb://localhost:27017/?readPreference=primary&ssl=false&retryWrites=true&w=majority&appname=NCAAFBetting"

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


def extract_state_and_number(line : str) -> tuple[str, int]:
    translator = str.maketrans("", "", string.punctuation)

    modified_string = line.translate(translator)

    #pattern = r'^\s*(\d+)\s+([A-Za-z\s]+)\s+=\s+(\d+\.\d+)\s+'
    pattern = r'^\s*\d+\s+([A-Za-z\s]+)\s+[A-Z]+\s+(\d+)\s+'

    match = re.match(pattern, modified_string)
    
    if match:
        team = match.group(1).strip()
        team = stdname(team)
        score = int(match.group(2))
        return team, score
    else:
        return None, None
    
        
def find_scores(list : list) -> dict:
    team_scores = {}
    for line in list:
        team, score = extract_state_and_number(line)
        if team and score:
            team_scores[team] = score
    return team_scores
        
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
    
    old_sagrin = collection.find_one({"sagrin": sagrin_content})
    old_vegas = collection.find_one({"vegas": vegas_content})
    return old_sagrin and old_vegas  
    
def find_game_scores(week_number):
    url = 'https://www.ncaa.com/scoreboard/football/fbs/2023/' + '{:02d}'.format(week_number) + '/all-conf'
    response = requests.get(url)
    
    soup = BeautifulSoup(response.content, 'html.parser')
    game_teams_ul_tags = soup.find_all('ul', class_='gamePod-game-teams')
        
    teams_and_scores = {}
        
    for ul_tag in game_teams_ul_tags:
        team_li_tags = ul_tag.find_all('li')
        team_data = []
            
        for li_tag in team_li_tags:
            team_name = li_tag.find('span', class_='gamePod-game-team-name').text.strip()
            team_name = stdname(team_name)
            team_score = li_tag.find('span', class_='gamePod-game-team-score').text.strip()
            if team_score == '':
                team_score = 0
            team_data.append((team_name, int(team_score)))
        teams_and_scores[(team_data[0][0], team_data[1][0])] = (team_data[0][1], team_data[1][1])
    return teams_and_scores
    


def run() -> list: 
    soup = scrape_sagrin()
    pre_tags = soup.find_all("pre")
    html_content = pre_tags[2].get_text()
    teams = html_content.splitlines()
    team_scores = find_scores(teams)

    soup = scrape_vegas_insider()
    tbody_tag = soup.find("tbody", id="odds-table-spread--0")
    game_odds = find_odds(tbody_tag) 

    data = []

    for teams, spreads in game_odds.items():
        away = stdname(teams[0])
        home = stdname(teams[1])
        if away not in team_scores:
            print(away + " not found. Needs name conversion")
        if home not in team_scores:
            print(home + " not found. Needs name conversion")
        prediction = team_scores[away] - team_scores[home] - 500
        
        
        diff = prediction/100.0 - spreads[0]
        diff = round(diff, 2)
        data.append(((away, home), diff, prediction/100.0, spreads[0]))

    return data


def update_bets():
    new_data = run()
    new_week = False
    #get current data from db if it exists
    #if it doesn't exist, create a new week
    #if it does exist, re-evaluate the week against the new data and update the db
    soup = scrape_vegas_insider()
    header_h2_text = soup.select('header.module-header.justified.flex-wrapped h2')
    text = header_h2_text[0].get_text()

    # Use regular expressions to extract the number from the text
    match = re.search(r'\d+', text)
    week_number = int(match.group())
   
    #get current week from db
    gameDB = client["game-database"] #database name
    weeks = gameDB["weeks-collection"] #collection name
    query = {"Num": week_number}
    week = weeks.find_one(query)
    if week == None:
        new_week = True
        
     
    if not new_week:
        old_games = week["Games"]
        for game in new_data:
            new_game = Game(week_number, game[0][1], game[0][0], game[3], game[2], False, 0, 0)
            game_match = next((g for g in old_games if g["_id"] == generate_game_id(new_game)), None)
            if game_match == None:
                print("BRHU")
                old_games.append(new_game.turn_to_dict())
            else:
                game_match["Spread"] = new_game.Spread
                game_match["Prediction"] = new_game.Prediction
        weeks.update_one(query, {"$set": {"Num Games": len(old_games)}})
        weeks.update_one(query, {"$set": {"Games": old_games}})

        update_scores(week_number)
        print("Week " + str(week_number) + " updated in database")

    else:
        games = []
        for game in new_data:
            new_game = Game(week_number, game[0][1], game[0][0], game[3], game[2], False, 0, 0)
            games.append(new_game)
        new_week = Week(week_number, games, 0, 0, len(new_data))
        weeks.insert_one(new_week.turn_to_dict())
        print("Week " + str(week_number) + " added to database")
        if week_number > 1:
            update_scores(week_number - 1)
            print("Old scores updated for week", week_number - 1)
            
    update_teams(week_number)

def update_scores(week_number):
    gameDB = client["game-database"] #database name
    weeks = gameDB["weeks-collection"] #collection name
    week = weeks.find_one({"Num": week_number})
 
    correct = 0
    incorrect = 0
    last_weeks_games = week["Games"]
    game_scores = find_game_scores(week_number)
    dbug_game_ctr = -1
    for game in last_weeks_games:
        dbug_game_ctr += 1
        home_team = game['Home']
        away_team = game['Away']
        if (away_team, home_team) not in game_scores:
            away_team, home_team = home_team, away_team
        if (away_team, home_team) not in game_scores:
            print("Could not find game: " + away_team + " at " + home_team + "\t\tGame idx: " + str(dbug_game_ctr))
            continue
        scores = game_scores[(away_team, home_team)]
        away_score = scores[0]
        home_score = scores[1]
        game["Away Score"] = away_score
        game['Home Score'] = home_score
        if home_score != 0 or away_score != 0:
            if game["Prediction"] < game["Spread"] and int(away_score) - int(home_score) < game["Spread"]:
                game["Success"] = True
                correct += 1
            elif game["Prediction"] > game["Spread"] and int(away_score) - int(home_score) > game["Spread"]:
                game["Success"] = True
                correct += 1
            else: 
                game["Success"] = False
                incorrect += 1
    #sys.exit()
    weeks.update_one({"Num": week_number}, {"$set": {"Games": last_weeks_games}})
    weeks.update_one({"Num": week_number}, {"$set": {"Correct": correct}})
    weeks.update_one({"Num": week_number}, {"$set": {"Incorrect": incorrect}})
def update_html():
    soup = scrape_sagrin()
    pre_tags = soup.find_all("pre")
    sagrin_content = pre_tags[2].get_text()
    
    soup = scrape_vegas_insider()
    vegas_content = soup.find("tbody", id="odds-table-spread--0").get_text()

    db = client["game-database"]
    collection = db["html_content"]
    collection.delete_many({})
    collection.insert_one({"sagrin": sagrin_content})
    collection.insert_one({"vegas": vegas_content})
    print("HTML updated")


def update_teams(week_number : int):
    gameDB = client["game-database"] #database name
    weeks = gameDB["weeks-collection"] #collection name
    query = {"Num": week_number}
    week = weeks.find_one(query)
    games = week["Games"]
    teams = gameDB["teams-collection"].find([])
    for game in games:
        if game["Home"] not in teams:
            gameDB["teams-collection"].insert_one({"Team": game["Home"], "Games": []})
        if game["Away"] not in teams:
            gameDB["teams-collection"].insert_one({"Team": game["Away"], "Games": []})
        teams[game["Home"]]["Games"].append(game)
        teams[game["Away"]]["Games"].append(game)
    for team in teams:
        gameDB["teams-collection"].update_one({"Team": team["Team"]}, {"$set": {"Games": team["Games"]}})
    print("Teams updated")
def update_db():
    update_bets()
    update_html()
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
### Database Schema ###
# week-collection
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
#
# html_content
# {
#   sagrin : string
#   vegas : string
# }
#
#
# team-collection
# {
#   Team : string
#   Games : [Game]
# }
#
# conference-collection
# {
#   Conference : string
#   Games : [Game]
# }
#

    