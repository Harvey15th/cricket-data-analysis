from json import load
from csv import DictReader, DictWriter
from os import listdir, path
from .team import team

def writeDict(dictArray, output_path):
    fieldnames = dictArray[0].keys()

    with open(output_path, mode="w", newline="", encoding="utf-8") as file:
        writer = DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dictArray)

def readDict(input_path):
    with open(input_path, 'r') as f:
        dict_reader = DictReader(f)
        dictArray = list(dict_reader)
    return dictArray

def prepare(input, output):
    Processed_2D = []

    for file in listdir(input):
        if file.endswith('.json'):
            with open(path.join(input, file), 'r') as f:
                matchData = load(f)

            processed_data = {}
            match_id = str(file)[:-5]
            date = matchData['info']['dates'][0]
            team_1 = matchData['info']['teams'][0]
            team_2 = matchData['info']['teams'][1]
            match_type = matchData['info']['match_type']
            try:
                winner = matchData['info']['outcome']['winner']
                processed_data = {'match_id' : match_id, 'date' : date, 'team1' : team_1, 'team2' : team_2, 'result' : winner, 'match_type' : match_type}
            except:
                result = matchData['info']['outcome']['result']
                processed_data = {'match_id' : match_id, 'date' : date, 'team1' : team_1, 'team2' : team_2, 'result' : result, 'match_type' : match_type}
            Processed_2D.append(processed_data)

    Processed_2D.sort(key = lambda x: x['date'])
    writeDict(Processed_2D, output)

def readData(input_path = None, elo_path = None):
    teams = []
    if elo_path is not None:
        teamsArray = readDict(elo_path)
        for teamDict in teamsArray:
            newTeam : team = team()
            newTeam.set_elo(teamDict['elo'])
            newTeam.set_matches_played(teamDict['matches_played'])
            teams.append([teamDict['name'], newTeam])

    if input_path is not None:
        matches = readDict(input_path)

        for match in matches:
            team1Name = match['team1']
            team2Name = match['team1']
            if team1Name not in teams:
                team1 = team()
                teams.append({team1Name : team1})
            if team2Name not in teams:
                team2 = team()
                teams.append({team2Name : team2})

    return teams, matches

def writeData(output_path, teams):
    teamDict = []

    for teamName in teams:
        tempTeam : team = teams[teamName]
        elo = tempTeam.get_elo()
        matches_played = tempTeam.get_matches_played()
        teamDict.append({'name' : teamName, 'elo' : elo, 'matches_played' : matches_played})

    writeDict(teamDict, output_path)
    return True
