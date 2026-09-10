'''Pure functions defining the mathematical model for evaluating elo rating score'''
import math

def expected_score(Ra, Rb):
    exponent = (Rb - Ra) / 400
    prob = 1 / (1 + math.pow(10, exponent))
    return prob

def score_for_team(result, team):
    if result == 'no result':
        return 'no result'
    elif result == 'tie':
        score = 0.5
    elif result == team:
        score = 1
    else:
        score = 0
    return score

def select_k_factor(games_played):
    return 64 if games_played >= 7 else 100

def adjust_elo(team1rating, team2rating, team1k, team2k, score):
    
    Ea = expected_score(team1rating, team2rating)
    change = score - Ea
    team1change = team1k * change
    team2change = team2k * -change
    return (team1rating + team1change, team2rating + team2change)
