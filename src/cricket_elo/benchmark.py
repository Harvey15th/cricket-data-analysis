from .train import train
from .model import adjust_elo, expected_score, score_for_team, select_k_factor
from typing import Dict, List

teamnames : List[str] = []
teams : Dict[str, List[int]] = {}
matches : Dict[int, List[str]] = {}
matchIDs : List[int] = []

def prepareData(input_filepath):
    with open(input_filepath, 'r') as f:
        match_data = f.readlines()
        f.close()

    for match in match_data:
        match = match.split(",")
        if match[2] not in teams:
            teams.update({match[2]: [1500, 0]})
            teamnames.append(match[2])
        if match[3] not in teams:
            teams.update({match[3]: [1500, 0]})
            teamnames.append(match[3])

        matches.update({match[0]: [match[2], match[3], match[4]]})
        matchIDs.append(match[0])

    matchIDs.sort()
    return

def benchmark(training_data, verification_data):

    input_data = training_data

    train(input_data, "outputs/validation_elos.csv")

    with open("outputs/validation_elos.csv", 'r') as f:
        for line in f.readlines():
            line = line.split(',')
            teams.update({line[0]: [int(line[1]), int(line[2])]})
            teamnames.append(line[0])

    prepareData(verification_data)

    squareError = 0
    length = len(matchIDs)

    for matchID in matchIDs:
        match = matches[matchID]
        team1 = teams[match]
        team2 = teams[match]
        prob = expected_score(int(team1[0]), int(team2[0]))

        score = score_for_team(match[2], match[0])
        if score == 'no result':
            continue
        
        squareError += (score - prob)**2

        Ka = select_k_factor(int(teams[match[0]][1]))
        Kb = select_k_factor((teams[match[1]][1]))

        teams[match[0]][0], teams[match[1]][0] = adjust_elo(int(team1[0]), int(team2[0]), Ka, Kb, score)
        teams[match[0]][1] += 1
        teams[match[1]][1] += 1

    squareError /= length
    print(f"Square Error is {squareError}")

    return True
        


