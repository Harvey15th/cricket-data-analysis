from .train import train
from .model import adjust_elo, expected_score, score_for_team, select_k_factor
from .csv_prepare import readData, writeDict
from .team import team

def verify_data(training_data, verification_data):
    trainTeams, trainMatches, result = train(training_data, writesFile = False)
    if not result:
        print("Train data not in chronological order")
        return None, None, False
        
    teams, matches = readData(input_path=verification_data, elos = trainTeams)
    
    if matches != sorted(matches, key = lambda x: (x["date"], x["match_id"])):
        print("Verification data not in chronological order")
        return teams, matches, False  
    
    matchIDs = []
    for match in trainMatches:
        matchIDs.append(match['match_id'])
    for match in matches:
        matchIDs.append(match['match_id'])
    
    if len(matchIDs) != len(set(matchIDs)):
        print("Repeat matches found")
        return teams, matches, False

    training_end = trainMatches[-1]['date']
    verification_start = matches[1]['date']
    if  training_end > verification_start:

        print("Training and Verification matches out of order")
        return teams, matches, False

    return teams, matches, True, training_end, verification_start
    
def benchmark(training_data, verification_data, output_path):
    teams, matches, result, training_end, verification_start = verify_data(training_data, verification_data)

    if not result:
        return False
    
    squareError = 0
    numberOfMatches = 0
    skippedMatches = 0

    for match in matches:
        team1Name = match['team1']
        team2Name = match['team2']
        team1 : team = teams[team1Name]
        team2 : team = teams[team2Name]

        prob = expected_score(team1.get_elo(), team2.get_elo())
        score = score_for_team(match['result'], team1Name)
        if score == 'no result' or score == 0.5:
            skippedMatches += 1
            continue

        numberOfMatches += 1
        squareError += (score - prob)**2

        Ka = select_k_factor(team1.get_matches_played())
        Kb = select_k_factor(team2.get_matches_played())

        team1elo, team2elo = adjust_elo(team1.get_elo(), team2.get_elo(), Ka, Kb, score)
        team1.set_elo(team1elo)
        team2.set_elo(team2elo)

        team1.add_match()
        team2.add_match()

    if numberOfMatches == 0:
        print("No matches with a result in evaluation")
        return False
    
    squareError /= numberOfMatches
    print(f"Square Error is {squareError}")

    evalLog = [{'brier_score' : squareError, 'matches_evaluated' : numberOfMatches, 'matches_skipped' : skippedMatches, 'training_end' : training_end, 'verification_start' : verification_start}]
    writeDict(evalLog, output_path)
    return True
        


