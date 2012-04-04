import collections, math

class LaplaceUnigramLanguageModel:

  def __init__(self, corpus):
    """Initialize your data structures in the constructor."""
    # TODO your code here
    self.laplaceUniGramCounts = collections.defaultdict(lambda: 0)
    self.total = 0
    self.train(corpus)

  def train(self, corpus):
    """ Takes a corpus and trains your language model. 
        Count total words
    """  
    # TODO your code here
    for sentence in corpus.corpus:
        for datum in sentence.data:
            token = datum.word
            self.laplaceUniGramCounts[token] = self.laplaceUniGramCounts[token] + 1
            self.total += 1

  def score(self, sentence):
    """ Takes a list of strings as argument and returns the log-probability of the 
        sentence using your language model. Use whatever data you computed in train() here.
    """
    # TODO your code here
    score = 0
    for token in sentence:
        count = self.laplaceUniGramCounts[token]
        score += math.log(count + 1)
        score -= math.log(self.total + len(self.laplaceUniGramCounts))
    return score
