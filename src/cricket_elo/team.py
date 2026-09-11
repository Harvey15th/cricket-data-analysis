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

    def get_matches_played(self):
        return self.matches_played

    def set_matches_played(self, newVal):
        self.matches_played = newVal