import math, collections

class LaplaceBigramLanguageModel:

  def __init__(self, corpus):
    """Initialize your data structures in the constructor."""
    # TODO your code here
    self.biGramCounts = collections.defaultdict(lambda: 0)
    self.uniGramCounts = collections.defaultdict(lambda: 0)
    self.train(corpus)

  def train(self, corpus):
    """ Takes a corpus and trains your language model. 
        Compute any counts or other corpus statistics in this function.
    """  
    # TODO your code here
    for sentence in corpus.corpus:
        datums = sentence.data
        for index in range(len(datums)):
            token_i = datums[index].word
            # count C(W_i_1)
            self.uniGramCounts[token_i] += 1
            if index > 0:
                # count C(W_i_1, W_i)
                token_i_1 = datums[index - 1].word
                bi_key = token_i_1 + "," + token_i
                self.biGramCounts[bi_key] += 1
            
  def score(self, sentence):
    """ Takes a list of strings as argument and returns the log-probability of the 
        sentence using your language model. Use whatever data you computed in train() here.
    """
    # TODO your code here
    score = 0
    v = 0
    for i in range(len(sentence )):
        if i > 0:
            bi_key = sentence[i - 1] + "," + sentence[i]
            count_bigram = self.biGramCounts[bi_key]
            count_unigram = self.uniGramCounts[sentence[i - 1]]
            score += math.log(count_bigram + 1)
            score -= math.log(count_unigram + len(self.biGramCounts))
    return score
