import urllib
import urllib2
import hashlib
import random
import email
import email.message
import email.encoders
import StringIO
import sys

class NullDevice:
  def write(self, s):
    pass

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
  partNames = ['Development Set', \
                'Test Set'
              ]
  return partNames


def sources():
  """Returns source files, separated by part. Each part has a list of files."""
  srcs = [ [ 'SpamLord.py' ], \
           [ 'SpamLord.py' ],
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
  login = raw_input('Login (Email address): ')
  password = raw_input('Password: ')
  return login, password


def homework_id():
  """Returns the string homework id."""
  return '1'


def getChallenge(email, partId):
  """Gets the challenge salt from the server. Returns (email,ch,state,ch_aux)."""
  url = challenge_url()
  values = {'email_address' : email, 'assignment_part_sid' : "%s-%s" % (homework_id(), partId), 'response_encoding' : 'delim'}
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
  return "https://www.coursera.org/nlp/assignment/challenge"

def submit_url():
  """Returns the submission url."""
  return "https://www.coursera.org/nlp/assignment/submit"

def submitSolution(email_address, ch_resp, part, output, source, state, ch_aux):
  """Submits a solution to the server. Returns (result, string)."""
  source_64_msg = email.message.Message()
  source_64_msg.set_payload(source)
  email.encoders.encode_base64(source_64_msg)

  output_64_msg = email.message.Message()
  output_64_msg.set_payload(output)
  email.encoders.encode_base64(output_64_msg)
  values = { 'assignment_part_sid' : ("%s-%s" % (homework_id(), part)), \
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

import SpamLord

def dumps_list_of_lists(res):
  s = '['
  for i, l in enumerate(res):
    if (i != 0):
      s += ', '
    s += '['
    for j, e in enumerate(l):
      if (j != 0):
        s += ', '
      s += '\"%s\"' % e
    s += ']'
  s += ']'
  return s

def output(partId, ch_aux):
  """Uses the student code to compute the output for test cases."""

  res = []
  # disable printing:
  original_stdout = sys.stdout
  sys.stdout = NullDevice()
  if(partId==1):
    train_data = ''
    res = SpamLord.process_dir('../data/dev')
  elif(partId==2):
    test_data = StringIO.StringIO(ch_aux)
    res = SpamLord.process_file('foo', test_data)
  else:
    sys.stdout = original_stdout
    print '[WARNING]\t[output]\tunknown partId: %s' % partId
  sys.stdout = original_stdout
  res_json = dumps_list_of_lists(res)
  return res_json

submit(0)
