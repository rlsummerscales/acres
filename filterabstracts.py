#!/usr/bin/env python
# author: Rodney Summerscales

import sys
import shutil
import glob

import xml.dom
import nltk.tokenize.treebank
import nltk.stem.wordnet
import xmlutil
import sentence
import tokenlist
import costvaluefinder
import lemmatizeabstracts

def keepForIschemiaCorpus(xmldoc):
    """ Return True if we should keep this abstract for the ischemia corpus
        Include abstract in ischemia corpus if it contains at least 4 integers.
    """
    textNodeList = xmldoc.getElementsByTagName('AbstractText')
    nIntegers = 0
    for textNode in textNodeList:
        text = xmlutil.getText(textNode)
        tokens = tokenizer.tokenize(text)
        for token in tokens:
            if token.isdigit():
                nIntegers += 1

    return nIntegers > 3

def keepForDiabetesCorpus(xmldoc):
    """ Return True if we should keep this abstract for the diabetes corpus
        Include abstract in diabetes corpus if it contains at least 4 integers.
    """
    textNodeList = xmldoc.getElementsByTagName('AbstractText')
    nCostValues = 0
    for textNode in textNodeList:
        text = xmlutil.getText(textNode)
        sentenceList = sentenceSplitter.tokenize(text)
        for sText in sentenceList:
            tokenTextList = tokenizer.tokenize(sText)
            tokenList = tokenlist.TokenList()
            tokenList.convertStringList(tokenTextList)
            s = sentence.Sentence(tokenList)
            for token in s:
                lemmatizeabstracts.lemmatizeToken(token)
                if cvFinder.tokenIsCostValue(token):
                    nCostValues += 1

    return nCostValues > 0

if len(sys.argv) < 3:
    print "Usage: filterabstracts.py <INPUT_PATH> <OUTPUT_PATH> <IGNORE_FILE>"
    print "Read MEDLINE XML abstracts in the directory specified by <INPUT_PATH>"
    print "Copy those abstracts that contain at least 4 integers to <OUTPUT_PATH>"
    print "Ignore abstracts found in the file <IGNORE_FILE>"
    sys.exit()

inputPath = sys.argv[1]
outputPath = sys.argv[2]

# build list of abstracts to ignore (possibly used in another corpus)
ignoreSet = set([])
if len(sys.argv) > 3:
    ignoreFile = sys.argv[3]
    file = open(ignoreFile, 'r')
    for line in file.readlines():
        [pmid, xml] = line.split('.')
        ignoreSet.add(pmid)

if inputPath[-1] != '/':
    inputPath += '/'
if outputPath[-1] != '/':
    outputPath += '/'

# initialize sentence splitter and tokenizer
sentenceSplitter = nltk.data.load('tokenizers/punkt/english.pickle')
tokenizer = nltk.tokenize.treebank.TreebankWordTokenizer()
lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()

cvFinder = costvaluefinder.CostValueFinder()

fileList = glob.glob(inputPath+'*.xml')
for filename in fileList:
    xmldoc = xml.dom.minidom.parse(filename)
    pmidNodes = xmldoc.getElementsByTagName('PMID')
    pmid = xmlutil.getText(pmidNodes[0])
    if pmid in ignoreSet:
        print pmid, 'already annotated'
    else:
        #        if keepForIschemiaCorpus(xmldoc):
        if keepForDiabetesCorpus(xmldoc):
            # copy abstract
            print 'Copying: ', filename
            shutil.copy(filename, outputPath)
