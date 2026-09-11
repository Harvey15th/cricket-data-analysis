from .team import team
from .model import adjust_elo, score_for_team, select_k_factor
from .csv_prepare import readData, writeData

def train(input_filepath, output_path):
    teams, matches = readData(input_path=input_filepath)

    for matchDict in matches:
        score = score_for_team(matchDict['result'], matchDict['team1'])

        if score != 'no result':
            team1 = teams[matchDict['team1']]
            team2 = teams[matchDict['team2']]

            Ka = select_k_factor(team1.get_matches_played())
            Kb = select_k_factor(team2.get_matches_played())

            team1elo, team2elo = adjust_elo(team1.get_elo(), team2.get_elo(), Ka, Kb, score)
            team1.set_elo(team1elo)
            team2.set_elo(team2elo)

            team1.add_match()
            team2.add_match()

    return writeData(output_path, teams)
