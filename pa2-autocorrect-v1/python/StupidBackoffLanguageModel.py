import math, collections

class StupidBackoffLanguageModel:
  # set k = 2 in stupid back off equation
  def __init__(self, corpus):
    """Initialize your data structures in the constructor."""
    # TODO your code here
    self.triGramCounts = collections.defaultdict(lambda: 0)
    self.biGramCounts = collections.defaultdict(lambda: 0)
    self.uniGramCounts = collections.defaultdict(lambda: 0)
    self.total = 0
    self.train(corpus)

  def train(self, corpus):
    """ Takes a corpus and trains your language model. 
        Compute any counts or other corpus statistics in this function.
    """  
    # TODO your code here
    for sentence in corpus.corpus:
        datums = sentence.data
        for i in range(len(datums)):
            self.total += 1
            token_i = datums[i].word
            self.uniGramCounts[token_i] += 1
            if i >= 1:
                token_i_1 = datums[i - 1].word
                bi_key = token_i_1 + "," + token_i
                self.biGramCounts[bi_key] += 1
                if i >= 2:
                    token_i_2 = datums[i - 2].word
                    tri_key = token_i_2 + "," + token_i_1 + "," + token_i
                    self.triGramCounts[tri_key] += 1

  def score(self, sentence):
    """ Takes a list of strings as argument and returns the log-probability of the 
        sentence using your language model. Use whatever data you computed in train() here.
    """
    # TODO your code here
    score = 0
    for i in range(len(sentence)):
        if i >= 1:
            bi_key = sentence[i - 1] + "," + sentence[i]
            count_bigram = self.biGramCounts[bi_key]
            count_unigram = self.uniGramCounts[sentence[i - 1]]
            if count_bigram > 0:
                score += math.log(count_bigram)
                score -= math.log(count_unigram)
            else:
                count_unigram = self.uniGramCounts[sentence[i]]
                score += math.log(count_unigram + 1)
                score -= math.log(self.total * 2)
                score += math.log(0.4)
    return score
