class Datum:
    def __init__(self, word, label):
        self.word = word
        self.label = label
        self.guessLabel = ''
        self.previousLabel = ''
        self.features = []
    
