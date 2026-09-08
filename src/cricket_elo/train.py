from team import team
from typing import List, Dict
import math

teamnames : Dict[str] = []
teams : Dict[str, team] = []
matches : Dict[int, List[str]] = {}
matchIDs : List[int] = []

def train(input_filepath, output_path):
    prepareData(input_filepath)

    for matchID in matchIDs:
        match = matches[matchID]
        adjust_elo(match[0], match[1], match[2])

    for teamname in teamnames:
        with open(output_path, 'a') as f:
            f.write(f'{teamname} elo: {teams[teamname].get_elo()}')

def adjust_elo(team1, team2, result):
    score = 0
    if result == 'no result':
        return
    elif result == 'tie':
        score = 0.5
    elif result == team1:
        score = 1
    else:
        score = 0

    Ea = expProb(team1.getElo(), team2.getElo())
    change = (score - Ea)

    Ka = 32 if team1.matchHistory().matches_played >= 7 else 100 - team1.matchHistory().matches_played
    Kb = 32 if team2.matchHistory().matches_played >= 7 else 100 - team2.matchHistory().matches_played

    team1.changeElo(change * Ka)
    team2.changeElo(-change * Kb)

def expProb(Ra, Rb):
    exponent = (Rb - Ra) / 400
    prob = 1 / (1 + math.Pow(10, exponent))
    return prob

def prepareData(input_filepath):
    with open(input_filepath, 'r') as f:
        match_data = f.readlines()
        f.close()

    for match in match_data:
        match.split(",")
        if match[2] not in teams:
            teams.update(match[2], team())
            teamnames.append(match[2])
        if match[3] not in teams:
            teams.update(match[3], team())
            teamnames.append(match[3])

        matches.update(match[0], [match[2], match[3], match[4]])
        matchIDs.append(match[0])

    matchIDs.sort()
    return