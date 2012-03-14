import sys
import os
import re
import pprint
"""
    complex case as follows:
    
    <td class="value">ouster (followed by &ldquo;@cs.stanford.edu&rdquo;)</td>
    <script> obfuscate('stanford.edu','jurafsky'); </script>
    <td class="value">teresa.lynn (followed by "@stanford.edu")</td>
    <dd>	<em>melissa&#x40;graphics.stanford.edu</em>
    <address>engler WHERE stanford DOM edu</address>
    email: pal at cs stanford edu,
    d-l-w-h-@-s-t-a-n-f-o-r-d-.-e-d-u
    <dd>	<em>ada&#x40;graphics.stanford.edu</em>
    Email: uma at cs dot stanford dot edu                                                 
    hager at cs dot jhu dot edu  
    funding at Stanford comes    
    (Fedora) Server at cs.stanford.edu Port 80                                                     
"""
my_email_pattern = r'''
                                                   # pattern for email
        (([\w-]+|[\w-]+\.[\w-]+)                   # hanks, justin.hanks, hanks-, justin-hanks-
        (\s.?\(f.*y.*)?                            # followed by 
        (\s?(@|&.*;)\s?|\s(at|where)\s)            # @, @ , at , where ,&#x40;,
        ([\w-]+|[\w-]+([\.;]|\sdo?t\s|\s)[\w-]+)   # gmail., ics.bjtu, ics;bjtu, ics dot bjtu, -ics-bjtu-
        ([\.;]|\s(do?t|DOM)\s|\s)                  # ., ;, dot , dt , DOM
        (-?e-?d-?u|com)\b)                         # .edu, .com, -e-d-u
        |
        (obfuscate\('(\w+\.edu)','(\w+)'\))        # obfuscate('stanford.edu','jurafsky')             
        '''
my_phone_pattern = r'''
                         # pattern for phone
        \(?(\d{3})\)?    # area code is 3 digits, e.g. (650), 650
        [ -]?            # separator is - or space or nothing, e.g. 650-XXX, 650 XXX, (650)XXX
        (\d{3})          # trunk is 3 digits, e.g. 800
        [ -]             # separator is - or space
        (\d{4})          # rest of number is 4 digits, e.g. 0987
        \D+              # should have at least one non digit character at the end
        '''
""" 
TODO
This function takes in a filename along with the file object (actually
a StringIO object at submission time) and
scans its contents against regex patterns. It returns a list of
(filename, type, value) tuples where type is either an 'e' or a 'p'
for e-mail or phone, and value is the formatted phone number or e-mail.
The canonical formats are:
     (name, 'p', '###-###-#####')
     (name, 'e', 'someone@something')
If the numbers you submit are formatted differently they will not
match the gold answers

NOTE: ***don't change this interface***, as it will be called directly by
the submit script

NOTE: You shouldn't need to worry about this, but just so you know, the
'f' parameter below will be of type StringIO at submission time. So, make
sure you check the StringIO interface if you do anything really tricky,
though StringIO should support most everything.
"""
def process_file(name, f):
    # note that debug info should be printed to stderr
    # sys.stderr.write('[process_file]\tprocessing file: %s\n' % (path))
    res = []
    for line in f:
        # match email
        matches = re.findall(my_email_pattern ,line, re.VERBOSE|re.I)
        for m in matches:
            email = ""
            if len(m[-1]) != 0:
                email = '%s@%s' % (m[-1], m[-2])
            else:
                if m[1] == "Server":
                    # skip "server at" sentence
                    continue
                email = '%s@%s.%s' % (m[1].replace("-", ""), 
                                      m[6].replace(";", ".")
                                          .replace(" dot ", ".")
                                          .replace("-", "")
                                          .replace(" ", "."), 
                                      m[-4].replace("-", ""))
            res.append((name,'e',email))
            
        # match phone number
        matches = re.findall(my_phone_pattern, line, re.VERBOSE)
        for m in matches:
            phone = '%s-%s-%s' % m
            res.append((name, 'p', phone))
            
    return res

"""
You should not need to edit this function, nor should you alter
its interface as it will be called directly by the submit script
"""
def process_dir(data_path):
    # get candidates
    guess_list = []
    for fname in os.listdir(data_path):
        if fname[0] == '.':
            continue
        path = os.path.join(data_path,fname)
        f = open(path,'r')
        f_guesses = process_file(fname, f)
        guess_list.extend(f_guesses)
    return guess_list

"""
You should not need to edit this function.
Given a path to a tsv file of gold e-mails and phone numbers
this function returns a list of tuples of the canonical form:
(filename, type, value)
"""
def get_gold(gold_path):
    # get gold answers
    gold_list = []
    f_gold = open(gold_path,'r')
    for line in f_gold:
        gold_list.append(tuple(line.strip().split('\t')))
    return gold_list

"""
You should not need to edit this function.
Given a list of guessed contacts and gold contacts, this function
computes the intersection and set differences, to compute the true
positives, false positives and false negatives.  Importantly, it
converts all of the values to lower case before comparing
"""
def score(guess_list, gold_list):
    guess_list = [(fname, _type, value.lower()) for (fname, _type, value) in guess_list]
    gold_list = [(fname, _type, value.lower()) for (fname, _type, value) in gold_list]
    guess_set = set(guess_list)
    gold_set = set(gold_list)

    tp = guess_set.intersection(gold_set)
    fp = guess_set - gold_set
    fn = gold_set - guess_set

    pp = pprint.PrettyPrinter(indent=4)
    #print 'Guesses (%d): ' % len(guess_set)
    #pp.pprint(guess_set)
    #print 'Gold (%d): ' % len(gold_set)
    #pp.pprint(gold_set)
    print 'True Positives (%d): ' % len(tp)
    pp.pprint(list(tp))
    print 'False Positives (%d): ' % len(fp)
    pp.pprint(list(fp))
    print 'False Negatives (%d): ' % len(fn)
    pp.pprint(list(fn))
    print 'Summary: tp=%d, fp=%d, fn=%d' % (len(tp),len(fp),len(fn))

"""
You should not need to edit this function.
It takes in the string path to the data directory and the
gold file
"""
def main(data_path, gold_path):
    guess_list = process_dir(data_path)
    gold_list =  get_gold(gold_path)
    score(guess_list, gold_list)

"""
commandline interface takes a directory name and gold file.
It then processes each file within that directory and extracts any
matching e-mails or phone numbers and compares them to the gold file
"""
if __name__ == '__main__':
    if (len(sys.argv) != 3):
        print 'usage:\tSpamLord.py <data_dir> <gold_file>'
        sys.exit(0)
    main(sys.argv[1],sys.argv[2])
    """
    if (len(sys.argv) == 3):
        main(sys.argv[1], sys.argv[2])
    else:
        main("../data/dev", "../data/devGOLD")
    """
    
    
