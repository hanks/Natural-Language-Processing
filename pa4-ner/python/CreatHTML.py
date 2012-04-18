comment = '''

The code in this file is public domain, except for a few places clearly marked
with comments saying where that particular piece of code was copied from.

The goal of this script is to make it simpler to evaluate features in 
Programming Assignment 4 of the Stanford Coursera course Natural Language 
Processing. This script creates a directory containing HTML files showing
the test corpus, the features used, and the FeatureFactory used to create
the features. In the corpus pages, one can hover the mouse on a word to get
information about the features active on that word. Some information
about the feature is also included. If a small patch is made to MEMM.java,
the weights of the feature is also shown (see below for a description of the
necessary changes).

To run this script, run the assignment code as usual, but make sure you include
the '-print' option and redirect the output to a file. E.g.

$ java -cp classes -Xmx1G NER ../data/train ../data/dev -print > myfile.txt

or

$ python NER.py ../data/train ../data/dev -print > myfile.txt

Then run this script using

$ python CreateHTML.py myoutputdirectory testWithFeatures.json myfile.txt

This will create a directory 'myoutputdirectory' where the HTML files will 
be written. You can also skip the last argument (myfile.txt in the above 
example) and create HTML with less information. In this case the classifier
is never run and this information is thus not included in the HTML files, but
you can still see some info about the features, like how many lines they match
for different classes.

The patch required is the following (this is the output from patch.exe for 
MEMM.java in the python directory, the MEMM.java in the java directory has 
some different comments but the code is the same apparently):

##########################################################################

26c26
<               List<Datum> testData = runMEMM(args[0], args[1]);
---
>               List<Datum> testData = runMEMM(args[0], args[1], print);
48a49,52
>       public static List<Datum> runMEMM(String trainFile,
>                       String testFile) throws IOException{
>               return runMEMM(trainFile, testFile, false);
>       }
50c54,55
<     public static List<Datum> runMEMM(String trainFile, String testFile) throws IOException{
---
>       public static List<Datum> runMEMM(String trainFile,
>                       String testFile, boolean printWeights) throws IOException{
69a75,94
>
>               if (printWeights) {
>                       System.out.println("---");
>                       int longestFeature = 0;
>                       for (int i = 0; i < obj.featureIndex.size(); i++) {
>                               int len = ((String)obj.featureIndex.get(i)).length();
>                               if (len > longestFeature) {
>                                       longestFeature = len;
>                               }
>                       }
>                       String formatString = "%-" + longestFeature + "s";
>                       for (int i = 0; i < weights[0].length; i++) {
>                               System.out.print(String.format(formatString, obj.featureIndex.get(i)));
>                               for (int j = 0; j < obj.labelIndex.size(); j++) {
>                                       System.out.print(String.format("  %+8.4f", weights[j][i]));
>                               }
>                               System.out.println();
>                       }
>                       System.out.println("---");
>               }

##########################################################################

In other words, what you need to do is 

1. send the boolean variable 'print' from the main method into the 
    runMEMM method.
2. add a boolean argument 'printWeights' to the runMEMM method.
3. create a new method runMEMM that looks exactly like the old one (i.e. before
    adding the printWeights argument) and calls the new one with 
    printWeights = false. This is needed because Submit.java calls that
    function and if it changes signature the compilation will fail.
4. add the 'if (printWeights)' statement to the method runMEMM. It goes between
    the lines creating the weights array and the line creating the Viterbi
    object.

'''


import time, json, base64, sys, os, os.path, re, textwrap, pdb, math, itertools
from cgi import escape
from itertools import chain

# Taken from itertools recipes
def flatten(listOfLists):
    "Flatten one level of nesting"
    return chain.from_iterable(listOfLists)

# Teken from http://www.zopyx.com/blog/a-python-decorator-for-measuring-the-execution-time-of-methods"
def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%s() %2.2f sec' % (method.__name__, te-ts)
        return result

    return timed
    
# Copied from Datum.py. Don't want the dependency since it makes it more
# annoying to use with Java.
class Datum:
    def __init__(self, word, label):
        self.word = word
        self.label = label
        self.guessLabel = ''
        self.previousLabel = ''
        self.features = []    
        
        
def log2(x): return math.log(x) / math.log(2.0)
        
        
def calculate_utility_measures(result, N, allLabels, labelToNumTokens):
    N10 = float(result[allLabels[0]])
    N11 = float(result[allLabels[1]])
    N00 = labelToNumTokens[allLabels[0]] - N10
    N01 = labelToNumTokens[allLabels[1]] - N11
    N_0 = N00 + N10
    N_1 = N01 + N11
    N0_ = N00 + N01
    N1_ = N10 + N11
    mutualInformation = (
        (0 if N11==0 else N11/N * log2(N*N11 / (N1_*N_1))) +
        (0 if N01==0 else N01/N * log2(N*N01 / (N0_*N_1))) +
        (0 if N10==0 else N10/N * log2(N*N10 / (N1_*N_0))) +
        (0 if N00==0 else N00/N * log2(N*N00 / (N0_*N_0))))
    if 0 == N10 == N11:
        chiSquare = 0
    elif 0 in [N_1, N1_, N_0, N0_]:
        chiSquare = float("inf")
    else:
        chiSquare = (
            (N11+N10+N01+N00) * (N11*N00 - N10*N01)**2 / 
            (N_1 * N1_ * N_0 * N0_))
    return mutualInformation, chiSquare            
    
@timeit
def getFeatureStats(trainDataWithFeatures, testDataWithFeatures):
    featureResult = {}
    allLabels = list(set(datum.label for datum in trainDataWithFeatures))
    assert (len(testDataWithFeatures)-1) % len(allLabels) == 0
    allFeatures = set.union(*(set(datum.features) 
                                for datum in trainDataWithFeatures))
    # featureResult is a dict with features as keys. The values are dicts with
    #   key is a label
    #   value is the number of times the feature was present for the key label                                
    featureResult = dict((feature, dict((label, 0) for label in allLabels))
                            for feature in allFeatures)
    labelToNumTokens = dict((label, 0) for label in allLabels)
    prevLabel = testDataWithFeatures[0].previousLabel
    for i in chain([0], xrange(1, len(testDataWithFeatures), len(allLabels))):
        if i>0:
            possibleDatums = testDataWithFeatures[i : i+len(allLabels)]
            possibleDatums = filter(lambda d: d.previousLabel==prevLabel, 
                possibleDatums)
            assert len(possibleDatums) == 1
            datum = possibleDatums[0]
        else:
            datum = testDataWithFeatures[0]
        labelToNumTokens[datum.label] += 1
        for feature in datum.features:
            # When running FeatureFactory on the test data, some features
            # not present in the train data can appear. These are ignored
            # in the Java code and thus ignored here too.
            if feature in featureResult:
                featureResult[feature][datum.label] += 1
        prevLabel = datum.label
                
    return featureResult, allLabels, labelToNumTokens    
    
@timeit
def parseJavaOutput(javaOutput):
    weights = {}          # {feature : (personWeight, oWeight)}
    classifications = []  # [(word, correctClass, classifierClass)]
    score = []            # [(s, float)] with s = "precision", "recall", or "F1"

    classificationRegexp = re.compile(r"^(\S+)\s+(O|PERSON)\s+(O|PERSON)\s*$")
    floatingPointRegexp = (
        r"inf|NaN|(?:[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)")
    weightRegexp = re.compile(r"^((?:\S.+)?\S+)\s+({0})\s+({0})\s*$".format(
        floatingPointRegexp))
    resultRegexp = re.compile(r"^(precision|recall|F1)\s*=\s*({})\s*$".format(
        floatingPointRegexp))
    for line in javaOutput.splitlines():
        classificationMatch = classificationRegexp.match(line)
        weightMatch = weightRegexp.match(line)
        resultMatch = resultRegexp.match(line)
        if classificationMatch:
            classifications.append(map(intern, classificationMatch.groups()))
        elif weightMatch:
            feature = weightMatch.group(1)
            oWeight, personWeight = map(float, weightMatch.groups()[1:])
            assert feature not in weights
            weights[feature] = (oWeight, personWeight)
        elif resultMatch:
            assert resultMatch.group(1) not in score
            score.append((resultMatch.group(1), float(resultMatch.group(2))))

    if len(score) != 3:
        print >>sys.stderr, "\n".join(textwrap.wrap(
            "Error: Could not find scores (precision, recall, and F1) in the "
            "file specified on the command line. Are you sure the "
            "javaOutputFile is the output of either NER.py, NER.java, or "
            "MEMM.java?"))
        sys.exit(1)
     
    if len(weights) == 0:
        print >>sys.stderr, "\n".join(textwrap.wrap(
            "Warning: No feature weights found. Have you patched MEMM.java as "
            "suggested at the top of CreateHTML.py?"))
        weights = None
    return score, weights, classifications
    
    

STYLE = '''
<style type="text/css">
<!--

a {
    cursor: default;
}

a:link {
    text-decoration: none;
}

a:visited {
    text-decoration:none;
}

a:active {
    text-decoration:none;
}

a:hover {
    text-decoration:underline;
    background: LightBlue;
}


table thead {
    font-weight: bold
}

table tfoot {
    font-weight: bold
}

table td {
    border-left:solid 10px transparent;
}

table td:first-child {
    border-left:0;
}

span#myid {
    display: none; 
    position: fixed; 
    top: 5px; 
    right: 5px; 
    padding: 5px; 
    margin: 10px; 
    z-index: 150; 
    background: #c0c0c0; 
    border: 1px dotted #c0c0c0;
}

-->
</style>
'''    


def getDatum(testDataWithFeatures, allLabels, index, label):
    assert isinstance(label, str)
    assert len(allLabels) > 0
    assert index >= 0
    if index == 0:
        return testDataWithFeatures[0]
    else:
        start = 1 + (index-1)*len(allLabels)
        return testDataWithFeatures[start + allLabels[label]]
   
@timeit   
def saveFeatureFactory(numPages, outputDirectory):
    if os.path.exists("FeatureFactory.py"):
        fileName = "FeatureFactory.py"
    elif os.path.exists("FeatureFactory.java"):
        fileName = "FeatureFactory.java"
    else:
        return False
        
    href = fileName+".html"
    html = ["<html><body><h1>{}</h1>".format(fileName)]
    
    pageSelectionHTML = createPageSelector(numPages, href, "FeatureFactory")
    html.append(pageSelectionHTML)
    html.append('<hr/><pre>')
    
    with open(fileName, "r") as f:
        for line in f:
            html.append(escape(line.rstrip("\r\n")))
    html.append("</pre></body></html>\n")
    
    with open(os.path.join(outputDirectory, href), "w") as f:
        f.write("\n".join(html))
    return href
        
        


INTRO = '''Holding the mouse over a word shows a popup in the upper right 
corner. The popup contains information about each of the features that are
"active" on that particular word. The feature properties are:'''

INFO = [('Feature', '''The name of the feature. The string you add in 
    FeatureFactory.'''),
    ('Weight O', '''The weight of the feature assigned by the 
    optimizer (MEMM.java) for the label O. *** means that this feature was not
    present when running with the training data and was thus never assigned
    a weight by the optimizer.'''),
    ('Weight PERSON', '''The weight of the feature for the label PERSON.'''),
    ('Matches O', '''The number of words of class O matched by this feature. 
    This is based on what the label of the previous word actually is (e.g. if 
    the previous word is of class O, only the features on the following word 
    with previous label O are counted).'''),
    ('Matches PERSON', '''The number of words of class PERSON matched by this
    feature.'''),
    ('Mutual Information', '''The mutual information for the feature, as defined
    in 'An Introduction to Information Retrieval'.'''),
    ('&Chi;<sup>2</sup>', '''The Chi-squared value for the feature, as defined
    in 'An Introduction to Information Retrieval'.'''),
    ('Bias', '''A value between -1 and +1 saying how large part of the words 
    from the classes O and PERSON the feature was active on. -1 means it was 
    only active for words in class O, +1 means the same for PERSON, 0 means it 
    was equally active for O and PERSON.'''),
    ('Feature Group Size', '''The size of the feature group this feature is part 
    of. A Feature Group is defined as the set of all features
    having the same name up until the first underscore in the name. By naming
    your features with this scheme in mind, you can more easily see how a 
    group of features is behaving. If you use names like 
    'CurrentWord_word='+currentWord you can track properties for that whole
    family of features.'''),
    ('Average &Chi;<sup>2</sup>', '''The (arithmetic) average of the features
    in the feature group this feature is in.'''),
    ('Average bias', '''The (arithmetic) average of the features
    in the feature group this feature is in.'''),
    ('Average predictability', '''The (arithmetic) average of the absolute 
    values of the biases of the features in the feature group this feature is 
    in.''')]
    
OUTRO = '''Below the weights is a <span style="font-weight: bold">Total</span> 
    row summing them up. Note
    that the classification of a word does not depend solely on the weights of
    the features for that word, but is (I think) a global optimum. This means
    that sometimes it looks like the weights make a certain classification but
    the word is actually classified as something else.'''
    
FEATURE_PROPERTIES_EXPLANATION = (
    '<div>{}</div><table><tbody>{}</tbody></table>{}'.format(
        INTRO, 
        "\n".join('''
                    <tr><td style="font-weight: bold">{}</td>
                    <td>{}</td>'''.format(
                column.replace(" ", "&nbsp;"), description) 
            for column, description in INFO),
        OUTRO))
       

def createPageSelector(numPages, featureFactoryHref, currentPage):
    assert currentPage in (
        range(numPages) + 
        (["FeatureFactory"] if featureFactoryHref else []) + 
        ["FeatureInformation"])
        
    pageSelectionHTML = ['<div align="center">Go to page</div>']
    pageSelectionHTML.append('<div align="center">'
        '<table border="1" rules="all"><tbody><tr>')
    if featureFactoryHref:
        pageSelectionHTML.append(
            '<td><a href="{0}">FeatureFactory</a></td>'.format(
                featureFactoryHref))
    pageSelectionHTML.append(
        '<td><a href="FeatureInformation.html">Feature Information</a></td>')
    for p in xrange(numPages):
        pageSelectionHTML.append('<td>')
        if p == currentPage:
            pageSelectionHTML.append("{}".format(p+1))
        else:
            pageSelectionHTML.append('<a href="{}.html">{}'.format(p, p+1))
        pageSelectionHTML.append('</td>')
    pageSelectionHTML.append('</tr></tbody></table></div>')
    pageSelectionHTML = "".join(pageSelectionHTML)    
    
    return pageSelectionHTML
        
def getAllLabels(testDataWithFeatures):    
    allLabelsSet = set()
    allLabels = []
    for datum in testDataWithFeatures:
        if datum.label not in allLabelsSet:
            allLabels.append(datum.label)
            allLabelsSet.add(datum.label)
    return allLabels
        
        
        
def getPageSplits(testDataWithFeatures, allLabels):
    """Returns a list with all the word indexes to split the corpus into 
    pages at. If you do pairwise(getPageSplits(...)) it will return the 
    startIndex and endIndex of the words in that page."""
    
    assert (len(testDataWithFeatures)-1) % len(allLabels) == 0
    numWords = (len(testDataWithFeatures) - 1) / len(allLabels) + 1
 
    approximateWordsPerPage = 8000
    numPages = int(round(float(numWords) / approximateWordsPerPage))
    numPages = max(numPages, 1)
    wordsPerPage = float(numWords) / numPages
    
    allLabelsDict = dict((label, index) for index,label in enumerate(allLabels))
    
    # List of all indexes of the first word on the pages, 
    # and the index past the last word
    pageSplitIndexes = (
        [int(i*wordsPerPage) for i in range(numPages)] + [numWords])
    # Move the pageSplitIndexes forward a little bit if there is an end of
    # sentence close by.
    for i in range(1, len(pageSplitIndexes)-1):
        for j in range(20):
            datum = getDatum(testDataWithFeatures, 
                            allLabelsDict, pageSplitIndexes[i]+j, allLabels[0])
            if datum.word in ".!?":
                pageSplitIndexes[i] += j+1
                break 
                
    assert sorted(pageSplitIndexes) == pageSplitIndexes, repr(pageSplitIndexes)                
    return pageSplitIndexes
   
@timeit
def generatePerWordHTML(testDataWithFeatures, 
        allLabels, classifications, colors):
    """Generate the HTML code for each word in the corpus. This includes the
    JavaScript call to a() and b() which shows the information about the word
    and the features active at that word. This function does not generate the
    function a() and b(), nor the data those functions use."""
    
    assert (len(testDataWithFeatures)-1) % len(allLabels) == 0
    numWords = (len(testDataWithFeatures) - 1) / len(allLabels) + 1    
    
    allLabelsDict = dict((label,index) for index,label in enumerate(allLabels)) 
    
    perWordHTML = []
    for i in xrange(numWords):
        if classifications:
            word, correctClass, guessClass = classifications[i]
            color = colors[(correctClass, guessClass)]
        else:
            datum = getDatum(testDataWithFeatures, 
                allLabelsDict, i, allLabels[0])
            word = datum.word
            color = colors[datum.label, datum.label]
        html = [('<a href="#" onmouseover="a({0});" '
                        + 'onmouseout="b({0});">').format(i),                    
                '<span style="color:{}">{}</span>'.format(
                        color, escape(word)),
                 '</a>']
            
        if word in ".!?":
            html.append("<br/>")
    
        perWordHTML.append("".join(html))    
    return perWordHTML
    
    
@timeit
def generateScriptForPage(startWordIndex, endWordIndex, testDataWithFeatures, 
        allLabels, classifications, weights, featureResult,
        featureInformation, featureGroups, featureGroupInformation):
    
    allLabelsDict = dict((label,index) for index,label in enumerate(allLabels))
    
    def jsEscape(s):
        return escape(s).replace("\\", "\\\\").replace('"', '\\"')
                
    jsWords = []
    jsCorrectLabels = []
    jsGuessLabels = []
    
    jsWordFeatures = []
    featureNameToIndex = {}
    jsFeatureInformation = []
    if startWordIndex == 0:
        jsPreviousPageLastGuessLabel = 0
    elif classifications:
        jsPreviousPageLastGuessLabel = allLabelsDict[
            classifications[startWordIndex-1][2]]
    else:
        jsPreviousPageLastGuessLabel = 0 # Doesn't matter, never used
    
    for i in range(startWordIndex, endWordIndex):
        if i == 0:
            prevLabel = allLabels[0]
        elif classifications:
            prevLabel = classifications[i-1][2]
        else:
            prevDatum = getDatum(testDataWithFeatures, 
                                allLabelsDict, i-1, allLabels[0])
            prevLabel = prevDatum.label
        datum = getDatum(testDataWithFeatures, allLabelsDict, i, prevLabel)
        jsWords.append(jsEscape(datum.word))
        jsCorrectLabels.append(allLabelsDict[datum.label])
        if classifications:
            jsGuessLabels.append(allLabelsDict[classifications[i][2]])
        else:
            jsGuessLabels.append(jsCorrectLabels[-1])
        jsWordFeatures.append([])
        
        for feature in sorted(datum.features):
            if feature not in featureNameToIndex:
                featureNameToIndex[feature] = len(jsFeatureInformation)
                featureGroup = feature.partition('_')[0]
                jsFeatureInformation.append(
                    [
                        '"{}"'.format(jsEscape(feature))] +
                    [weights[feature][i] if weights and feature in weights 
                                            else '"***"'
                        for i in range(len(allLabels))] +
                    [featureResult[feature][label] 
                        for label in allLabels] +
                    [
                        "%.5f"%featureInformation[feature][0],
                        "%.3f"%featureInformation[feature][1],
                        "%.3f"%featureInformation[feature][2],
                        len(featureGroups[featureGroup]),
                        "%.3f"%featureGroupInformation[featureGroup][1],
                        "%.3f"%featureGroupInformation[featureGroup][2],
                        "%.3f"%featureGroupInformation[featureGroup][3]
                    ])
            featureIndex = featureNameToIndex[feature]
            jsWordFeatures[-1].append(featureNameToIndex[feature])                  

    def jsListContents(format, seq):
        return ",".join(format.format(e) for e in seq)
        
    script = r'''
        var startIndex = {startWordIndex};
        
        var hasTrueWeights = {hasTrueWeights};
        var hasClassifications = {hasClassifications};
        
        var columnNames = ["Feature", {weightColumnNames},
                        {matchesColumnNames},
                        "Mutual Information", "&Chi;<sup>2</sup>",
                        "Bias", "Feature Group Size", 
                        "Average &Chi;<sup>2</sup>", "Average bias",
                        "Averiage predictability"];
        var allLabels = [{allLabels}];               
        var words = [{words}];
        var previousPageLastGuessLabel = {previousPageLastGuessLabel};
        var correctLabels = [{correctLabels}];
        var guessLabels = [{guessLabels}];
        
        var wordFeatures = [{wordFeatures}];
        
        var featureInformation = [{featureInformation}];

    '''.format(startWordIndex=startWordIndex,
            hasTrueWeights="true" if weights else "false",
            hasClassifications="true" if classifications else "false",
            weightColumnNames = ",".join('"Weight {}"'.format(c)
                for c in allLabels),
            matchesColumnNames = ",".join('"Matches {}"'.format(c)
                for c in allLabels),
            allLabels=jsListContents('"{}"', allLabels),
            words=jsListContents('"{}"', jsWords),
            previousPageLastGuessLabel=jsPreviousPageLastGuessLabel,
            correctLabels=",".join(map(str, jsCorrectLabels)),
            guessLabels=",".join(map(str, jsGuessLabels)),
            wordFeatures=",".join(
                '[{}]'.format(",".join(map(str, wf)))
                    for wf in jsWordFeatures),
            featureInformation=",".join(
                "[{}]".format(",".join(map(str, fi))) 
                    for fi in jsFeatureInformation)) + r'''
                
        function a(n) {
            var span = document.getElementById("myid");
            var cl = correctLabels[n-startIndex];
            var gl = guessLabels[n-startIndex];
            var pl = n==startIndex ? previousPageLastGuessLabel : 
                                    guessLabels[n-startIndex-1];
            var html = "<h3>" + words[n-startIndex] + "</h3>" + 
                "<div>Index " + n + ", ";
            if (hasClassifications) {
                html += allLabels[cl] + " " +
                            (cl==gl ? "correctly" : "incorrectly") + 
                            " labeled as " + allLabels[gl] + 
                            ", previous word classified as " + 
                            allLabels[pl];
            }
            else {
                html += "class " + allLabels[cl];
            }
            html += "</div>\n";
            html += "<table border=\"1\", rules=\"none\" cellpadding=\"2\">";
            html += "<thead>";
            html += "<tr>\n";
            var i=0;
            for (i=0; i<columnNames.length; i++) {
                if (i>=1 && i<1+allLabels.length && !hasTrueWeights) {
                    continue;
                }                
                html += "<td align=\"" + (i==0 ? "left" : "right") + 
                        "\">" + columnNames[i] + "</td>";
            }
            html += "</tr></thead>\n<tbody>";
            var features = wordFeatures[n-startIndex];
            var weights = [];
            for (i=0; i<allLabels.length; i++) {
                weights[i] = 0.0;
            }
            for (i=0; i<features.length; i++) {
                html += "<tr>";
                var featureIndex = features[i];
                var columns = featureInformation[featureIndex];
                var j=0;
                for (j=0; j<columns.length; j++) {
                    if (j>=1 && j<1+allLabels.length && !hasTrueWeights) {
                        continue;
                    }
                    else if (j>=1 && j<1+allLabels.length) {
                        var w = parseFloat(columns[j]);
                        if (!isNaN(w)) {
                            weights[j-1] += w;
                        }                    
                    }
                    html += "<td align=\"" + (j==0 ? "left" : "right") + 
                        "\">" + columns[j] + "</td>";
                }
                html += "</tr>\n";
            }
            html += "</tbody>";
            if (hasTrueWeights) {
                html += "<tfoot><tr><td align=\"left\">Total</td>";
                for (i=0; i<allLabels.length; i++) {
                    html += "<td align=\"right\">" + weights[i].toFixed(3) + 
                                "</td>";
                }
                for (i=3; i<columnNames.length; i++) {
                    html += "<td></td>";
                }
                html += "</tr>\n</tfoot>";
            }
            html += "</table>";
            span.innerHTML = html;
            span.style.display = "block";
        }
        
        function b(n) {
            var span = document.getElementById("myid");
            span.style.display = "none";     
        }
    '''    
    
    return script
    
    
def getColorHtml(colors, hasClassification):
    colorHtml = []
    for classes, color in colors.items():
        if hasClassification:
            colorHtml.append('''
                <font color="{color}">{color}</font> - 
                word of class {correctClass} {correctIncorrect} classified
                as {guessClass}<br/>\n'''.format(
                    color=color,
                    correctClass=classes[0],
                    guessClass=classes[1],
                    correctIncorrect=("correctly" 
                        if classes[0]==classes[1] else "incorrectly")))
        elif classes[0]==classes[1]:
            colorHtml.append('''
                <font color="{color}">{color}</font> -
                word of class {class_}<br/>\n'''.format(
                    color=color,
                    class_=classes[0]))
    return "".join(colorHtml)
    
@timeit
def getFeatureInformation(featureResult, labelToNumTokens, allLabels):
    assert len(labelToNumTokens) == len(allLabels)
    
    numWords = sum(labelToNumTokens.values())

    # {feature : [features]}
    featureGroups = {}
    
    # {feature : (mutualInformation, chiSquare, bias)}
    featureInformation = {}
    for feature, result in featureResult.iteritems():
        featureGroup = feature.partition("_")[0]
        featureGroups.setdefault(featureGroup, []).append(feature)
        
        mutualInformation, chiSquare = calculate_utility_measures(
            result, numWords, allLabels, labelToNumTokens)
        biasDenominator = result[allLabels[0]] + result[allLabels[1]]
        if biasDenominator != 0:
            bias = 2.0*result[allLabels[1]] / biasDenominator - 1
        else:
            bias = 0
        featureInformation[feature] = (mutualInformation, chiSquare, bias)
    
    # featureGroupInformation: {featureGroup: (averageMutualInformation, 
    #                   averageChiSquare, averageBias, averagePredictability)}
    featureGroupInformation = {}
    for featureGroup, features in featureGroups.iteritems():
        features.sort()
        mis, chiSquares, biases = zip(
            *[featureInformation[f] for f in features])
        averageMutualInformation = sum(mis) / len(mis)
        averageChiSquare = sum(chiSquares) / len(chiSquares)
        averageBias = sum(biases) / len(biases)
        averagePredictability = sum(map(abs, biases)) / len(biases)
        featureGroupInformation[featureGroup] = (averageMutualInformation, 
            averageChiSquare, averageBias, averagePredictability)            
    
    return featureInformation, featureGroups, featureGroupInformation
    
@timeit
def writeFeatureInformation(outputDirectory, numCorpusPages, featureFactoryHref, 
        featureResult, featureInformation, 
        featureGroups, featureGroupInformation, 
        allLabels, weights):
    
    
    pageSelectionHtml = createPageSelector(numCorpusPages, 
        featureFactoryHref, "FeatureInformation")    
        
        
    featureGroupHtml = ['''<table><thead><tr>
        <td>Name</td>
        <td>Num features</td>''']
    if weights:
        for label in allLabels:
            featureGroupHtml.append('<td>Average weight {}</td>'.format(
                label))
    featureGroupHtml.append('''
            <td>Average mutual information</td>
            <td>Average &Chi;<sup>2</sup></td>
            <td>Average bias</td>
            <td>Average predictability</td>
        </thead><tbody>''')
    for name, features in sorted(featureGroups.iteritems()):
        assert len(features) > 0
        if len(features) == 1:
            continue
        featureGroupHtml.append('<tr>')
        featureGroupHtml.append('<td>{}</td>'.format(name))
        featureGroupHtml.append('<td>{}</td>'.format(len(features)))
        if weights:
            for i in range(len(allLabels)):
                featureWeights = [weights[feature][i]
                    for feature in features if feature in weights]
                averageWeight = (sum(featureWeights) / len(featureWeights))
                featureGroupHtml.append('<td>{:.3f}</td>'.format(averageWeight))
        for property,precision in zip(featureGroupInformation[name], [5,3,3,3]):
            featureGroupHtml.append('<td>{:.{precision}f}</td>'.format(
                property, precision=precision))
        featureGroupHtml.append('</tr>')
    featureGroupHtml.append('</tbody></table>')
    
    
    featureHtml = ['''<table><thead><tr>
        <td>Name</td>''']
    if weights:
        for label in allLabels:
            featureHtml.append('<td>Weight {}</td>'.format(label))
    for label in allLabels:
        featureHtml.append('<td>Matches {}</td>'.format(label))            
    featureHtml.append('''
            <td>Mutual information</td>
            <td>&Chi;<sup>2</sup></td>
            <td>Bias</td>
        </tr>        
        </thead><tbody>''')
    for name,info in sorted(featureInformation.iteritems()):
        featureHtml.append('<tr>')
        featureHtml.append('<td>{}</td>'.format(name))        
        if weights:
            if name in weights:
                for i in range(len(allLabels)):
                    featureHtml.append('<td>{}</td>'.format(weights[name][i]))
            else:
                featureHtml.append('<td>***</td>')
        for label in allLabels:
            featureHtml.append('<td>{}</td>'.format(featureResult[name][label]))
        featureHtml.append(''' 
            <td>{:.5f}</td>
            <td>{:.3f}</td>
            <td>{:.3f}</td>'''.format(*info))
        featureHtml.append('</tr>')
    featureHtml.append('</tbody></table>')
    
    style = '''            
        <style type="text/css">
            <!--
                table thead {
                    font-weight: bold
                }

                table tfoot {
                    font-weight: bold
                }

                table td {
                    border-left:solid 10px transparent;
                    text-align:right
                }

                table td:first-child {
                    border-left:0;
                    text-align:left
                }    
            -->
        </style>'''  
        
    html = '''
        <html>
        <head>
            <title>Feature information</title>
            {style}
        </head>
        <body>
            <h1>Feature information</h1>
            <div>Number of features: {numberOfFeatures}</div>
            <div>Number of feature groups: {numberOfFeatureGroups} (of which
                {numberOfSingleFeatureGroups} contains only one feature and are 
                not included in the Feature Groups list below)</div>
            <div>Go to <a href="#Features">Features</a></div>
            {pageSelector}
            <h2>Feature Groups</h2>
            {featureGroups}        
            <div><a name="Features"><h2>Features</h2></a></div>
            {features}        
        </body>
        </html>'''.format(
            style=style,
            numberOfFeatures=len(featureInformation),
            numberOfFeatureGroups=len(featureGroups),
            numberOfSingleFeatureGroups=
                len(filter(lambda x: len(x)==1, featureGroups.itervalues())),
            pageSelector=pageSelectionHtml,
            featureGroups="\n".join(featureGroupHtml),
            features="\n".join(featureHtml))
            
    with open(os.path.join(outputDirectory, 
            "FeatureInformation.html"), "w") as f:
        f.write(html)            
            
        
@timeit 
def createHTML(testDataWithFeatures, javaOutput, outputDirectory):
    allLabels = getAllLabels(testDataWithFeatures)
    if (len(testDataWithFeatures)-1) % len(allLabels) != 0:
        print >>sys.stderr, "\n".join(textwrap.wrap((
            "The json input has an invalid number of entries - {}. The number "
            "of entries after the first entry must "
            "be divisible by the number of labels ({}) in the file.").format(
                len(testDataWithFeatures), len(allLabels))))
        sys.exit(1)        

    numWords = (len(testDataWithFeatures)-1)/len(allLabels) + 1
        
    if javaOutput:
        totalScore, weights, classifications = parseJavaOutput(javaOutput)
        # testDataWithFeatures is assumed to be in the order 
        # O, O, PERSON, O, PERSON, O, PERSON
        if len(classifications) != numWords:
            print >>sys.stderr, "\n".join(textwrap.wrap((
                "The number of words in the json and java output doesn't "
                "match. The json file contains {} entries (equivalent to {} "
                "words (all except the first with {} previous labels), the "
                "java output contains {} words.").format(
                    len(testDataWithFeatures), numWords, len(allLabels),
                    len(classifications))))
            sys.exit(1)
    else:
        totalScore = weights = classifications = None
    
    allLabelsDict = dict((label, index) for index,label in enumerate(allLabels))
    
    featureResult, _, labelToNumTokens = getFeatureStats(
        testDataWithFeatures, testDataWithFeatures)
        
    featureInformation, featureGroups, featureGroupInformation = (
        getFeatureInformation(featureResult, labelToNumTokens, allLabels))
  
    # colors = {(correctClass, guessClass) : color}
    colors = dict(zip(
        itertools.product(allLabels, repeat=2),
        ["Grey", "Red", "DarkOrange", "Black"]))
    #colors = {
    #    ("O", "O") : "Grey",
    #    ("PERSON", "PERSON") : "Black",
    #    ("O", "PERSON") : "Red",
    #    ("PERSON", "O") : "DarkOrange"}
        
    buildTime = time.strftime("%Y-%m-%d %H:%M:%S")

    perWordHTML = generatePerWordHTML(testDataWithFeatures, 
        allLabels, classifications, colors)
        
    pageSplitIndexes = getPageSplits(testDataWithFeatures, allLabels)
    numPages = len(pageSplitIndexes)-1
        
    if not os.path.exists(outputDirectory):
        os.mkdir(outputDirectory)            
    featureFactoryHref = saveFeatureFactory(numPages, outputDirectory)
    writeFeatureInformation(outputDirectory, numPages, featureFactoryHref, 
        featureResult, featureInformation, 
        featureGroups, featureGroupInformation, 
        allLabels, weights)
    for page in xrange(numPages):
        startWordIndex = pageSplitIndexes[page]
        endWordIndex = pageSplitIndexes[page+1]     

        pageSelectionHtml = createPageSelector(numPages, 
            featureFactoryHref, page)
            
        script = generateScriptForPage(startWordIndex, endWordIndex, 
                testDataWithFeatures, 
                allLabels, classifications, weights, featureResult,
                featureInformation, featureGroups, featureGroupInformation)
             
        hasClassifications = classifications is not None
        colorHtml = getColorHtml(colors, hasClassifications)
        
        scoreHtml = "" if not totalScore else "".join(
            '{} = {}<br/>\n'.format(*s) for s in totalScore)

        html = '''
            <html>
            <head>
                <title>NLP Programming Assignment 4 Result - Page {page}</title>                
                {style} 
                <script>
                    {script}
                </script>
            </head>
            <body>
                <span id="myid">
                    Popup info box placeholder...
                </span>
                <h1>NLP Programming Assignment 4 Result - Page {page}</h1>
                <p>Time: {time}</p>
                {score}
                <h3>Classification Colors</h3>
                {colors}
                <hr/>
                {propertiesExplanation}
                {pageSelection}
                <hr/>
                <div style="cursor: default;">
                    {words}
                </div>
                <hr/>
                {pageSelection}
                <hr/>
            </body></html>
            \n'''.format(style=STYLE, 
                script=script,
                page=page+1,
                time=escape(buildTime),
                score=scoreHtml,
                colors=colorHtml,
                propertiesExplanation=FEATURE_PROPERTIES_EXPLANATION,
                pageSelection=pageSelectionHtml,
                words="\n".join(perWordHTML[startWordIndex:endWordIndex]))
             
        with open(os.path.join(outputDirectory, "%d.html"%page), "w") as f:
            f.write(html)
                

@timeit         
def readTestDataWithFeatures(fileName):
    result = []
    with open(fileName, "r") as jsonFile:
        for line in jsonFile:
            jsonObj = json.loads(line)
            word = intern(base64.b64decode(jsonObj['_word']))
            label = intern(str(jsonObj['_label']))
            datum = Datum(word, label)
            datum.previousLabel = intern(str(jsonObj['_prevLabel']))
            
            featureObj = jsonObj['_features']
            for feature in featureObj.itervalues():
                datum.features.append(intern(str(feature)))
                
            result.append(datum)            
    return result
            
@timeit
def main(argv):
    if len(argv) not in [2,3]:
        print "Usage:"
        print ("CreateHTML.py <outputDir> <testWithFeatures.json> "
                "[javaOutputFile.txt] ")
        sys.exit(0)
        
    outputDir_arg = argv[0]
    testWithFeatures_arg = argv[1]
    javaOutputFile_arg = None if len(argv)==2 else argv[2]
    
    testDataWithFeatures = readTestDataWithFeatures(testWithFeatures_arg)
    if not testDataWithFeatures:
        print >>sys.stderr, "File %s is empty!" % testWithFeatures_arg
        sys.exit(1)
        
    if len(argv) > 2:
        if (os.path.getmtime(javaOutputFile_arg) < 
                os.path.getmtime(testWithFeatures_arg)):
            print >>sys.stderr, "\n".join(textwrap.wrap(
                "Modification time of java output file '{}' is earlier "
                "than modification time of '{}' file! This means that "
                "the java output file can not have been generated by the "
                "json file, and you supply two files from the "
                "same 'run'. Please run NER.py or NER.java again to rewrite "
                "the files.".format(
                    javaOutputFile_arg, testWithFeatures_arg)))
        with open(javaOutputFile_arg, "r") as javaOutputFile:
            javaOutput = javaOutputFile.read()
        if not javaOutputFile:
            print >>sys.stderr, "File %s is empty!" % javaOutputFile_arg
            sys.exit(1)
    else:
        javaOutput = None
        
    if os.path.exists(outputDir_arg) and not os.path.isdir(outputDir_arg):
        print >>sys.stderr, (
            "Output dir '%s' is not a directory!" % outputDir_arg)
        sys.exit(1)
        
    createHTML(testDataWithFeatures, javaOutput, outputDir_arg)
    


if __name__ == '__main__':
    main(sys.argv[1:])