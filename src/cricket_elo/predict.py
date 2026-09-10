from typing import Dict, List
import math

teamnames : List[str] = []
teams : Dict[str, List[int]] = {}

def predict(args):

    input_filepath = args.ratings
    team1 = args.team_a
    team2 = args.team_b
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