import urllib
import urllib2
import hashlib
import random
import email
import email.message
import email.encoders


def submit(partId):   
  print '==\n== [nlp] Submitting Solutions | Programming Exercise %s\n=='% homework_id()
  if(not partId):
    partId = promptPart()

  partNames = validParts()
  if not isValidPartId(partId):
    print '!! Invalid homework part selected.'
    print '!! Expected an integer from 1 to %d.' % (len(partNames) + 1)
    print '!! Submission Cancelled'
    return
  
  (login, password) = loginPrompt()
  if not login:
    print '!! Submission Cancelled'
    return
  
  print '\n== Connecting to coursera ... '

  # Setup submit list
  if partId == len(partNames) + 1:
    submitParts = range(1, len(partNames) + 1) 
  else:
    submitParts = [partId]

  for partId in submitParts:
    # Get Challenge
    (login, ch, state, ch_aux) = getChallenge(login, partId)
    if((not login) or (not ch) or (not state)):
      # Some error occured, error string in first return element.
      print '\n!! Error: %s\n' % login
      return

    # Attempt Submission with Challenge
    ch_resp = challengeResponse(login, password, ch)
    (result, string) = submitSolution(login, ch_resp, partId, output(partId, ch_aux), \
                                    source(partId), state, ch_aux)
    print '\n== [nlp] Submitted Homework %s - Part %d - %s' % \
          (homework_id(), partId, partNames[partId - 1]),
    print '== %s' % string.strip()



def promptPart():
  """Prompt the user for which part to submit."""
  print('== Select which part(s) to submit: ' + homework_id())
  partNames = validParts()
  srcFiles = sources()
  for i in range(1,len(partNames)+1):
    print '==   %d) %s [ %s ]' % (i, partNames[i - 1], srcFiles[i - 1])
  print '==   %d) All of the above \n==\nEnter your choice [1-%d]: ' % \
          (len(partNames) + 1, len(partNames) + 1)
  selPart = raw_input('') 
  partId = int(selPart)
  if not isValidPartId(partId):
    partId = -1
  return partId 


def validParts():
  """Returns a list of valid part names."""

  partNames = [ 'Laplace Unigram Dev', \
                'Laplace Unigram Test', \
                'Laplace Bigram Dev', \
                'Laplace Bigram Test', \
                'Stupid Backoff Dev', \
                'Stupid Backoff Test', \
                'Custom Dev', \
                'Custom Test'
              ]
  return partNames


def sources():
  """Returns source files, separated by part. Each part has a list of files."""
  srcs = [ [ 'LaplaceUnigramLanguageModel.py', 'SpellCorrect.py'], \
           [ 'LaplaceUnigramLanguageModel.py', 'SpellCorrect.py'], \
           [ 'LaplaceBigramLanguageModel.py', 'SpellCorrect.py'], \
           [ 'LaplaceBigramLanguageModel.py', 'SpellCorrect.py'], \
           [ 'StupidBackoffLanguageModel.py', 'SpellCorrect.py'], \
           [ 'StupidBackoffLanguageModel.py', 'SpellCorrect.py'], \
           [ 'CustomLanguageModel.py', 'SpellCorrect.py'], \
           [ 'CustomLanguageModel.py', 'SpellCorrect.py'],
         ]
  return srcs

def isValidPartId(partId):
  """Returns true if partId references a valid part."""
  partNames = validParts()
  return (partId and (partId >= 1) and (partId <= len(partNames) + 1))


# =========================== LOGIN HELPERS ===========================

def loginPrompt():
  """Prompt the user for login credentials. Returns a tuple (login, password)."""
  (login, password) = basicPrompt()
  return login, password


def basicPrompt():
  """Prompt the user for login credentials. Returns a tuple (login, password)."""
  #login = raw_input('Login (Email address): ')
  #password = raw_input('Password: ')
  login = "zhouhan315@gmail.com"
  password = "UwBMgxSXTe"
  return login, password


def homework_id():
  """Returns the string homework id."""
  return '2'


def getChallenge(email, partId):
  """Gets the challenge salt from the server. Returns (email,ch,state,ch_aux)."""
  url = challenge_url()
  values = {'email_address' : email, 'assignment_part_sid' : "%s-%d" % (homework_id(), partId), 'response_encoding' : 'delim'}
  data = urllib.urlencode(values)
  req = urllib2.Request(url, data)
  response = urllib2.urlopen(req)
  text = response.read().strip()

  # text is of the form email|ch|signature
  splits = text.split('|')
  if(len(splits) != 9):
    print 'Badly formatted challenge response: %s' % text
    return None
  return (splits[2], splits[4], splits[6], splits[8])



def challengeResponse(email, passwd, challenge):
  sha1 = hashlib.sha1()
  sha1.update("".join([challenge, passwd])) # hash the first elements
  digest = sha1.hexdigest()
  strAnswer = ''
  for i in range(0, len(digest)):
    strAnswer = strAnswer + digest[i]
  return strAnswer 
  
  

def challenge_url():
  """Returns the challenge url."""
  return "https://www.coursera.org/nlp/assignment/challenge";


def submit_url():
  """Returns the submission url."""
  return "https://www.coursera.org/nlp/assignment/submit";

def submitSolution(email_address, ch_resp, part, output, source, state, ch_aux):
  """Submits a solution to the server. Returns (result, string)."""
  source_64_msg = email.message.Message()
  source_64_msg.set_payload(source)
  email.encoders.encode_base64(source_64_msg)

  output_64_msg = email.message.Message()
  output_64_msg.set_payload(output)
  email.encoders.encode_base64(output_64_msg)
  values = { 'assignment_part_sid' : ("%s-%d" % (homework_id(), part)), \
             'email_address' : email_address, \
             #'submission' : output, \
             'submission' : output_64_msg.get_payload(), \
             #'submission_aux' : source, \
             'submission_aux' : source_64_msg.get_payload(), \
             'challenge_response' : ch_resp, \
             'state' : state \
           }
  url = submit_url()  
  data = urllib.urlencode(values)
  req = urllib2.Request(url, data)
  response = urllib2.urlopen(req)
  string = response.read().strip()
  # TODO parse string for success / failure
  result = 0
  return result, string

def source(partId):
  """Reads in the source files for a given partId."""
  src = ''
  src_files = sources()
  if partId <= len(src_files):
    flist = src_files[partId - 1]              
    for fname in flist:
      # open the file, get all lines
      f = open(fname)
      src = src + f.read() 
      f.close()
      src = src + '||||||||'
  return src

############ BEGIN ASSIGNMENT SPECIFIC CODE ##############


from HolbrookCorpus import HolbrookCorpus
from UnigramLanguageModel import UnigramLanguageModel
from StupidBackoffLanguageModel import StupidBackoffLanguageModel
from LaplaceUnigramLanguageModel import LaplaceUnigramLanguageModel
from LaplaceBigramLanguageModel import LaplaceBigramLanguageModel
from CustomLanguageModel import CustomLanguageModel
from SpellCorrect import SpellCorrect


def output(partId, ch_aux):
  """Uses the student code to compute the output for test cases."""

  trainCorpus = HolbrookCorpus('../data/holbrook-tagged-train.dat')
  testCorpus = HolbrookCorpus()
  testCorpus.slurpString(ch_aux) 
  lm = None
  if partId == 1 or partId == 2:
    lm = LaplaceUnigramLanguageModel(trainCorpus) 
  elif partId == 3 or partId == 4:
    lm = LaplaceBigramLanguageModel(trainCorpus) 
  elif partId == 5 or partId == 6:
    lm = StupidBackoffLanguageModel(trainCorpus)
  elif partId == 7 or partId == 8:
    lm = CustomLanguageModel(trainCorpus)
  else:
    print 'Unknown partId: " + partId'
    return None

  speller = SpellCorrect(lm, trainCorpus)
  output = speller.correctCorpus(testCorpus)
  # put in the part ID as well
  output = '[["%d"],%s' % (partId, output[1:])
  return output

submit(0)
