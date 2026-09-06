class team:
    def __init__(self):
        self.elo = 1500
        self.matches_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0

    def update_elo(self, change):
        self.elo += change

    def get_elo(self):
        return self.elo

    def record_match(self, result):
        self.matches_played += 1
        if result == 'win':
            self.wins += 1
        elif result == 'loss':
            self.losses += 1
        elif result == 'draw':
            self.draws += 1
    
    def match_history(self):
        return {
            'matches_played': self.matches_played,
            'wins': self.wins,
            'losses': self.losses,
            'draws': self.draws
        }