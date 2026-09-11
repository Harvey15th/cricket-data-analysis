from .model import expected_score
from .csv_prepare import readData
from .team import team

def predict(ratings, team1Name, team2Name):

    teams, _ = readData(elo_path=ratings)

    if team1Name not in teams or team2Name not in teams:
        return False
    else:
        team1 : team = teams[team1Name]
        team2 : team = teams[team2Name]
        prob = expected_score(team1.get_elo(), team2.get_elo())

        print(f'{team1Name} has a {round(prob*100)}% chance of winning')
        return True