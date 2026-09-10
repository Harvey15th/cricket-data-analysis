class team:
    def __init__(self):
        self.elo = 1500
        self.matches_played = 0

    def update_elo(self, change):
        self.elo += change

    def get_elo(self):
        return self.elo

    def set_elo(self, elo):
        self.elo = elo
        
    def add_match(self):
        self.matches_played += 1

    def match_history(self):
        return {
            'matches_played': self.matches_played,
        }