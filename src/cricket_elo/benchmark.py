from .train import train
from .model import adjust_elo, expected_score, score_for_team, select_k_factor
from .csv_prepare import readData, writeDict
from .team import team

def verify_data(training_data, verification_data):
    trainTeams, trainMatches, result = train(training_data, writesFile = False)
    teams, matches = readData(input_path=verification_data, elos = trainTeams)
    
    try:
        training_end = trainMatches[-1]['date']
        verification_start = matches[0]['date']
    except:
        print("Empty files")
        return None, None, False, None, None
    if not result:
        print("Train data not in chronological order")
        return None, None, False, None, None



    if matches != sorted(matches, key = lambda x: (x["date"], x["match_id"])):
        print("Verification data not in chronological order")
        return teams, matches, False, None, None
    
    matchIDs = []
    for match in trainMatches:
        matchIDs.append(match['match_id'])
    for match in matches:
        matchIDs.append(match['match_id'])
    
    if len(matchIDs) != len(set(matchIDs)):
        print("Repeat matches found")
        return teams, matches, False, None, None

    if  training_end > verification_start:

        print("Training and Verification matches out of order")
        return teams, matches, False, training_end, verification_start
    
    if training_end == verification_start:

        training_endID = trainMatches[-1]['match_id']
        verification_startID = matches[0]['match_id']
        if training_endID > verification_startID:
            return None, None, False, None, None

    return teams, matches, True, training_end, verification_start
    
def benchmark(training_data, verification_data, output_path, predictions_output = None):
    teams, matches, result, training_end, verification_start = verify_data(training_data, verification_data)

    if not result:
        return False

    baselineSquareError = 0
    squareError = 0
    numberOfMatches = 0
    skippedMatches = 0
    evalLog = []

    for match in matches:
        team1Name = match['team1']
        team2Name = match['team2']
        team1 : team = teams[team1Name]
        team2 : team = teams[team2Name]

        elo_team1_before = team1.get_elo()
        elo_team2_before = team2.get_elo()

        prob = expected_score(team1.get_elo(), team2.get_elo())
        score = score_for_team(match['result'], team1Name)

        result = match['result']
        status = 'evaluated' if score == 0 or score == 1 else ('tie' if score == 0.5 else 'no_result')
        actual_score = None if status == 'no_result' else score
        elo_brier = (score - prob)**2 if status == 'evaluated' else None
        baseline_brier = (score - 0.5)**2 if status == 'evaluated' else None

        if predictions_output:
            evalLog.append({'match_id' : match['match_id'], 'date' : match['date'], 'team1' : team1Name, 'team2' : team2Name,
                        'result' : result, 'elo_team1_before' : elo_team1_before, 
                        'elo_team2_before' : elo_team2_before, 'p_team1' : prob, 
                        'actual_score' : actual_score, 'status' : status, 'elo_brier' : elo_brier, 
                        'baseline_brier' : baseline_brier})

        if score == 'no result':
            skippedMatches += 1
            continue

        Ka = select_k_factor(team1.get_matches_played())
        Kb = select_k_factor(team2.get_matches_played())

        team1elo, team2elo = adjust_elo(elo_team1_before, elo_team2_before, Ka, Kb, score)

        team1.set_elo(team1elo)
        team2.set_elo(team2elo)

        team1.add_match()
        team2.add_match()

        if score == 0.5:
            skippedMatches += 1
            continue
        else:
            baselineSquareError += (score - 0.5)**2
            squareError += (score - prob)**2
            numberOfMatches += 1
    if numberOfMatches == 0:
        print("No matches with a result in evaluation")
        return False
    
    squareError /= numberOfMatches
    baselineSquareError /= numberOfMatches
    improvement = baselineSquareError - squareError
    print(f"Square Error is {squareError}")

    evalResults = [{'brier_score' : squareError, 'baseline_brier_score' : baselineSquareError, 'brier_improvement' : improvement, 'matches_evaluated' : numberOfMatches, 'matches_skipped' : skippedMatches, 'training_end' : training_end, 'verification_start' : verification_start}]
    writeDict(evalResults, output_path)

    if predictions_output:
        writeDict(evalLog, predictions_output)
    return True
        


