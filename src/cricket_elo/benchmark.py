from .train import adjust_elo, train, expProb
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

def benchmark(args):

    input_data = args.training_data
    verification_data = args.verification_data
    
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
        team1 = teams[matches[matchID][0]]
        team2 = teams[matches[matchID][1]]
        prob = expProb(int(team1[0]), int(team2[0]))

        if matches[matchID][2] == 'no result':
            continue
        elif matches[matchID][2] == 'tie':
            score = 0.5
        elif matches[matchID][2] == team1:
            score = 1
        else:
            score = 0
        squareError += (score - prob)**2

        Ka = 64 if int(teams[matches[matchID][0]][1]) >= 7 else 100
        Kb = 64 if int(teams[matches[matchID][1]][1]) >= 7 else 100

        teams[matches[matchID][0]][1] += 1
        teams[matches[matchID][1]][1] += 1

        teams[matches[matchID][0]][0] += (score-prob) * Ka
        teams[matches[matchID][1]][0] += (prob-score) * Kb

    squareError /= length
    print(f"Square Error is {squareError}")

    return True
        


