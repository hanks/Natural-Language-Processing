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
    if (string.strip() == 'Exception: We could not verify your username / password, please try again. (Note that your password is case-sensitive.)'):
      print '== The password is not your login, but a 10 character alphanumeric string displayed on the top of the Assignments page'



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

  partNames = [ 'Named Entity Recognition Dev', \
                'Named Entity Recognition Test'
              ]
  return partNames


def sources():
  """Returns source files, separated by part. Each part has a list of files."""
  srcs = [ ['FeatureFactory.py'], \
           ['FeatureFactory.py']
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
  return '4'


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
  #return 'https://stanford.campus-class.org/lang2info/assignment/challenge'
  #return "https://www.coursera.org/nlp-staging/assignment/challenge"
  return "https://www.coursera.org/nlp/assignment/challenge"


def submit_url():
  """Returns the submission url."""
  #return 'https://stanford.campus-class.org/lang2info/assignment/submit'
  #return "https://www.coursera.org/nlp-staging/assignment/submit"
  return "https://www.coursera.org/nlp/assignment/submit"

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

from FeatureFactory import FeatureFactory
from subprocess import Popen, PIPE
import os

def output(partId, ch_aux):
  """Uses the student code to compute the output for test cases."""
  print '== Running your code ...'

  featureFactory = FeatureFactory()

  # read the train and test data
  trainData = featureFactory.readData("../data/train")
  testData = featureFactory.readTestData(ch_aux)
  
  # add the features
  trainDataWithFeatures = featureFactory.setFeaturesTrain(trainData);
  testDataWithFeatures = featureFactory.setFeaturesTest(testData);

  # write the updated data into JSON files
  featureFactory.writeData(trainDataWithFeatures, "trainWithFeaturesSubmit");
  featureFactory.writeData(testDataWithFeatures, "testWithFeaturesSubmit");

  # run MEMM 
  output = Popen(['java','-cp', 'classes', '-Xmx1G' ,'MEMM'
                  ,'trainWithFeaturesSubmit.json', 'testWithFeaturesSubmit.json',
                  '-submit'], stdout=PIPE).communicate()[0]
  # print output[:100]
  os.remove('trainWithFeaturesSubmit.json')
  os.remove('testWithFeaturesSubmit.json')

  print '== Finished running your code'

  return output

submit(0)
