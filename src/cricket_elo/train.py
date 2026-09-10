from .team import team
from .model import adjust_elo, score_for_team, select_k_factor
from typing import List, Dict
import math

teamnames : List[str] = []
teams : Dict[str, team] = {}
matches : Dict[int, List[str]] = {}
matchIDs : List[int] = []

def train(input_filepath, output_path):
    prepareData(input_filepath)

    for matchID in matchIDs:
        match = matches[matchID]
        score = score_for_team(match[2], match[0])

        if score != 'no result':
            Ka = select_k_factor(teams[match[0]].match_history()['matches_played'])
            Kb = select_k_factor(teams[match[1]].match_history()['matches_played'])

            team1elo, team2elo = adjust_elo(teams[match[0]].get_elo(), teams[match[1]].get_elo(), Ka, Kb, score)
            teams[match[0]].set_elo(team1elo)
            teams[match[1]].set_elo(team2elo)

            teams[match[0]].add_match()
            teams[match[1]].add_match()

    for teamname in teamnames:
        with open(output_path, 'a') as f:
            f.write(f'{teamname},{round(teams[teamname].get_elo())},{teams[teamname].match_history()['matches_played']}\n')

    return True

def prepareData(input_filepath):
    with open(input_filepath, 'r') as f:
        match_data = f.readlines()
        f.close()

    for match in match_data:
        match = match.split(",")
        if match[2] not in teams:
            teams.update({match[2]: team()})
            teamnames.append(match[2])
        if match[3] not in teams:
            teams.update({match[3]: team()})
            teamnames.append(match[3])

        matches.update({match[0]: [match[2], match[3], match[4]]})
        matchIDs.append(match[0])

    matchIDs.sort()
    return