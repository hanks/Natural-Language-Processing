import json, sys
import base64
import re
import collections
from Datum import Datum

class FeatureFactory:
    """
    Add any necessary initialization steps for your features here
    Using this constructor is optional. Depending on your
    features, you may not need to intialize anything.
    """
    def __init__(self):
        self.readNameList()


    """
    Words is a list of the words in the entire corpus, previousLabel is the label
    for position-1 (or O if it's the start of a new sentence), and position
    is the word you are adding features for. PreviousLabel must be the
    only label that is visible to this method. 
    """

    def readNameList(self):
        self.names = collections.defaultdict(lambda:0)
        
        f = open("../data/male.txt")
        for name in f:
            name = name.strip()
            self.names[name] += 1
        f.close()
        
        f = open("../data/female.txt")
        for name in f:
            name = name.strip()
            self.names[name] += 1
        f.close()
        
        
    def computeFeatures(self, words, previousLabel, position):
        features = []
        currentWord = words[position]

        """ Baseline Features """
        features.append("word=" + currentWord)
        features.append("prevLabel=" + previousLabel)
        features.append("word=" + currentWord + ", prevLabel=" + previousLabel)
	"""
        Warning: If you encounter "line search failure" error when
        running the program, considering putting the baseline features
	back. It occurs when the features are too sparse. Once you have
        added enough features, take out the features that you don't need. 
	"""


	""" TODO: Add your features here """
        '''
        Justin
        R'Hanks
        Justin Hanks
        Hanks said
        Justin-Hanks
        Justin var Hanks
        '''
    
       
        singleNamePattern = r'''
            #^[A-Z]([A-Za-z]+)?$  # Peter, John
        '''
        if re.match(singleNamePattern, currentWord, re.VERBOSE) is not None:
            features.append("Titlecase")
        
        if self.names[currentWord] != 0:
            features.append("personName")
        '''
        wordShapePattern = r'''
           # ^.*?[A-Z]+[a-z]+$
        '''
        l = list(currentWord)
        l.sort()
        str = "".join(l)
        if re.match(wordShapePattern, str, re.VERBOSE):
            features.append("wordshape")
        '''
        
        #if currentWord.endswith("'s"):
        #    features.append("word=" + currentWord[:currentWord.find("'s")])
            
            
            
        '''
        singleNamePattern = r'''
            #^[A-Z][a-z]+$  # Peter, John
        '''
        if re.match(singleNamePattern, currentWord, re.VERBOSE) is not None:
            features.append("PERSON")
            
        hyphentedNamePattern = r'''
            #^[A-Z][a-z]+-[A-Z][a-z]+$ # Justin-Hanks
        '''
        if re.match(hyphentedNamePattern, currentWord, re.VERBOSE) is not None:
            features.append("PERSON")
            
        apostrophiesName = r'''
            #^[A-Z]'[A-Z][a-z]+$ # R'Hanks
        '''
        if re.match(apostrophiesName, currentWord, re.VERBOSE) is not None:
            features.append("PERSON")
            
        #if position + 1 < len(words):
        #    if re.match(singleNamePattern, currentWord, re.VERBOSE) is not None and re.match(singleNamePattern, words[position + 1], re.VERBOSE) is not None: 
        #        features.append("JointNameFirst")
          
        if position + 1 < len(words):      
            if words[position + 1] == "said":
                features.append("PERSON")   
            
        #if position > 0:
        #    if re.match(singleNamePattern, currentWord, re.VERBOSE) is not None and re.match(singleNamePattern, words[position - 1], re.VERBOSE) is not None: 
        #        features.append("JointNameBackoff")
                
        '''
        return features

    """ Do not modify this method """
    def readData(self, filename):
        data = [] 
        
        for line in open(filename, 'r'):
            line_split = line.split()
            # remove emtpy lines
            if len(line_split) < 2:
                continue
            word = line_split[0]
            label = line_split[1]

            datum = Datum(word, label)
            data.append(datum)

        return data

    """ Do not modify this method """
    def readTestData(self, ch_aux):
        data = [] 
        
        for line in ch_aux.splitlines():
            line_split = line.split()
            # remove emtpy lines
            if len(line_split) < 2:
                continue
            word = line_split[0]
            label = line_split[1]

            datum = Datum(word, label)
            data.append(datum)

        return data


    """ Do not modify this method """
    def setFeaturesTrain(self, data):
        newData = []
        words = []

        for datum in data:
            words.append(datum.word)

        ## This is so that the feature factory code doesn't
        ## accidentally use the true label info
        previousLabel = "O"
        for i in range(0, len(data)):
            datum = data[i]

            newDatum = Datum(datum.word, datum.label)
            newDatum.features = self.computeFeatures(words, previousLabel, i)
            newDatum.previousLabel = previousLabel
            newData.append(newDatum)

            previousLabel = datum.label

        return newData

    """
    Compute the features for all possible previous labels
    for Viterbi algorithm. Do not modify this method
    """
    def setFeaturesTest(self, data):
        newData = []
        words = []
        labels = []
        labelIndex = {}

        for datum in data:
            words.append(datum.word)
            if not labelIndex.has_key(datum.label):
                labelIndex[datum.label] = len(labels)
                labels.append(datum.label)
        
        ## This is so that the feature factory code doesn't
        ## accidentally use the true label info
        for i in range(0, len(data)):
            datum = data[i]

            if i == 0:
                previousLabel = "O"
                datum.features = self.computeFeatures(words, previousLabel, i)

                newDatum = Datum(datum.word, datum.label)
                newDatum.features = self.computeFeatures(words, previousLabel, i)
                newDatum.previousLabel = previousLabel
                newData.append(newDatum)
            else:
                for previousLabel in labels:
                    datum.features = self.computeFeatures(words, previousLabel, i)

                    newDatum = Datum(datum.word, datum.label)
                    newDatum.features = self.computeFeatures(words, previousLabel, i)
                    newDatum.previousLabel = previousLabel
                    newData.append(newDatum)

        return newData

    """
    write words, labels, and features into a json file
    Do not modify this method
    """
    def writeData(self, data, filename):
        outFile = open(filename + '.json', 'w')
        for i in range(0, len(data)):
            datum = data[i]
            jsonObj = {}
            jsonObj['_label'] = datum.label
            jsonObj['_word']= base64.b64encode(datum.word)
            jsonObj['_prevLabel'] = datum.previousLabel

            featureObj = {}
            features = datum.features
            for j in range(0, len(features)):
                feature = features[j]
                featureObj['_'+feature] = feature
            jsonObj['_features'] = featureObj
            
            outFile.write(json.dumps(jsonObj) + '\n')
            
        outFile.close()

