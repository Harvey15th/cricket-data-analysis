from typing import Dict, List
import math

teamnames : List[str] = []
teams : Dict[str, List[int]] = {}

def predict(input_filepath, team1, team2):
    with open(input_filepath, 'r') as f:
        for line in f.readlines():
            line = line.split(',')
            teams.update({line[0]: [int(line[1]), int(line[2])]})
            teamnames.append(line[0])

    if team1 not in teamnames or team2 not in teamnames:
        return False
    else:
        exponent = (teams[team2][0] - teams[team1][0]) / 400
        prob = 1 / (1 + math.pow(10, exponent))

        print(f'{team1} has a {round(prob*100)}% chance of winning')
        return True