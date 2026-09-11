from .train import train
from .model import adjust_elo, expected_score, score_for_team, select_k_factor
from .csv import readData
from .team import team

TRAINED_ELOS = "outputs/validation_elos.csv"

def benchmark(training_data, verification_data):

    train(training_data, TRAINED_ELOS)
    teams, matches = readData(input_path=verification_data, elo_path=TRAINED_ELOS)

    squareError = 0
    length = len(matches)

    for match in matches:
        team1Name = match['team1']
        team2Name = match['team2']
        team1 : team = teams[team1Name]
        team2 : team = teams[team2Name]

        prob = expected_score(team1.get_elo(), team2.get_elo())
        score = score_for_team(match['result'], team1Name)
        if score == 'no result':
            continue
        
        squareError += (score - prob)**2

        Ka = select_k_factor(team1.get_matches_played())
        Kb = select_k_factor(team2.get_matches_played())

        team1elo, team2elo = adjust_elo(team1.get_elo(), team2.get_elo(), Ka, Kb, score)
        team1.set_elo(team1elo)
        team2.set_elo(team2elo)

        team1.add_match()
        team2.add_match()

    squareError /= length
    print(f"Square Error is {squareError}")

    return True
        


