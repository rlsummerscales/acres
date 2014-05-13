#!/usr/bin/python
# Find mentions in a collection of texts
# author: Rodney Summerscales

import sys
import os.path
import random
import math
import nltk
from nltk.corpus import stopwords

from abstract import loadAbstractFile
from abstract import writeXML
from abstract import mentionTypes
from crossvalidate import CrossValidationSets


# keep track of important n-grams for an abstract
class KeyTerms:
  unigramCounts = {}
  bigramCounts = {}
  trigramCounts = {}
  termWeights = {}
  nTokens = 0        # total number of tokens in abstract
 
  def __init__(self, abs):
    self.unigramCounts = {}
    self.bigramCounts = {}
    self.trigramCounts = {}
    self.termWeights = {}
    self.nTokens = 0
  
    # count number of unigramCounts and bigramCounts occurrences in abstract
    for sentence in abs.sentences:
      for i in range(0, len(sentence.tokens)):
        self.nTokens = self.nTokens + 1
        term1 = sentence.tokens[i].getTerm()
        if len(term1) > 0:
          # skip numbers
          if term1 in self.unigramCounts:
            self.unigramCounts[term1] = self.unigramCounts[term1] + 1
          else:
            self.unigramCounts[term1] = 1
            self.bigramCounts[term1] = {}
            self.trigramCounts[term1] = {}
          if i+1 < len(sentence.tokens):
            term2 = sentence.tokens[i+1].getTerm()
            if len(term2) > 0:
              if term2 in self.bigramCounts[term1]:
                self.bigramCounts[term1][term2] = self.bigramCounts[term1][term2]+1
              else:
                self.bigramCounts[term1][term2] = 1
                self.trigramCounts[term1][term2] = {}
              if i+2 < len(sentence.tokens):
                term3 = sentence.tokens[i+2].getTerm()
                if len(term3) > 0:
                  if term3 in self.trigramCounts[term1][term2]:
                    self.trigramCounts[term1][term2][term3] = \
                      self.trigramCounts[term1][term2][term3] +1
                  else:
                    self.trigramCounts[term1][term2][term3] = 1
                  
  # calculate the weights for all unigrams in sentence given
  # the number of document occurrences of each unigram
  # and the number of documents
  def computeWeights(self, docUnigramCounts, nDoc):
    self.termWeights = {}
    for term in self.unigramCounts:
      tf = float(self.unigramCounts[term])/self.nTokens
      idf = math.log(nDoc/docUnigramCounts.get(term, 0.1))
      w = tf*idf
      self.termWeights[term] = w 
         
# keep track of important n-grams in list of abstracts
class KeyTermLists:
  keyTerms = {}           # lists of key terms for each abstract
#  docUnigramCounts = {}   # number of abstracts in training set that
                          # a given term appears in
#  nDoc = 0                # number of abstracts in train set
  avgWeight = 0           # the average term weight in list of abstracts
  stdDev = 0              # standard deviation in term weight
  ignoreTokens=set(['`', ',', '.', '/', '(', ')', '$', '%', ':', ';', '=',\
                      '>', '<', 'v'])

  # build lists of keyterms for each abstract in absList
  # use trainAbsList for calculating term distribution
  def __init__(self, trainAbsList, absList):
    self.keyTerms = {}
    docUnigramCounts = {}
    nDoc = len(trainAbsList)
    
    # count n-gram occurrences in training corpus
    for abs in trainAbsList: 
      keyTerms = KeyTerms(abs)
      for term in keyTerms.unigramCounts:
        if term in docUnigramCounts:
          docUnigramCounts[term] = docUnigramCounts[term] + 1
        else:
          docUnigramCounts[term] = 1
    
    # identify key terms in given set of abstracts
    wSum = 0
    nTerms = 0
    for abs in absList:
      self.keyTerms[abs.id] = KeyTerms(abs)
      self.keyTerms[abs.id].computeWeights(docUnigramCounts, nDoc)
      for w in self.keyTerms[abs.id].termWeights.values():
        wSum = wSum + w 
      nTerms = nTerms + len(self.keyTerms[abs.id].termWeights)
      
    # compute average term weight within test corpus
    self.avgWeight = wSum / nTerms
    
    # compute stdev
    ssd = 0
    for abs in absList:
      for w in self.keyTerms[abs.id].termWeights.values():
        ssd = ssd + (w-self.avgWeight)*(w-self.avgWeight)   
    self.stdDev = math.sqrt(ssd/nTerms)
    
    
    
  # return True if a given token is considered a key term for a given abstract
  def isKeyTerm(self, token, abs):
    term = token.getTerm()
    if abs.id not in self.keyTerms:
      print 'WARNING: cannot find', abs.id, 'in list of abstracts'
      return False
    
    return self.termIsSpecial(term, abs.id)

  # return True if a given term is considered special for abstract with
  # given abstract id
  def termIsSpecial(self, term, absId):
    threshold = self.avgWeight + self.stdDev
    if term in self.keyTerms[absId].termWeights \
      and self.keyTerms[absId].termWeights[term] > threshold:
      # term has greater than avg weight
      return True
    else:
      return False
      
  # return true if a given token bigram a key bigram in an abstract
  def isKeyBigram(self, token1, token2, abs):  
    term1 = token1.getTerm()
    term2 = token2.getTerm()
    if abs.id not in self.keyTerms:
      print 'WARNING: cannot find', abs.id, 'in list of abstracts'
      return False

    return self.bigramIsSpecial(term1, term2, abs.id)

  # return True if a given bigram is considered special for given abstract
  def bigramIsSpecial(self, term1, term2, absId):
    if term1 in self.keyTerms[absId].bigramCounts \
      and term2 in self.keyTerms[absId].bigramCounts[term1] \
      and self.keyTerms[absId].bigramCounts[term1][term2] > 3 \
      and self.uncommonWord(term1) and self.uncommonWord(term2):
      return True
    else:
      return False

  # return true if a given token trigram a key bigram in an abstract
  def isKeyTrigram(self, token1, token2, token3, abs):  
    term1 = token1.getTerm()
    term2 = token2.getTerm()
    term3 = token3.getTerm()
    if abs.id not in self.keyTerms:
      print 'WARNING: cannot find', abs.id, 'in list of abstracts'
      return False

    return self.trigramIsSpecial(term1, term2, term3, abs.id)

  # return True if a given trigram is considered special for given abstract
  def trigramIsSpecial(self, term1, term2, term3, absId):
    if term1 in self.keyTerms[absId].trigramCounts \
      and term2 in self.keyTerms[absId].trigramCounts[term1] \
      and term3 in self.keyTerms[absId].trigramCounts[term1][term2] \
      and self.keyTerms[absId].trigramCounts[term1][term2][term3] > 3 \
      and self.uncommonWord(term1) and self.uncommonWord(term2) \
      and self.uncommonWord(term3):
      return True
    else:
      return False
      
  # return true if a given word/token is not in a list of things to ignore    
  def uncommonWord(self, word):
    if word in self.ignoreTokens: # or word in stopwords.words('english'):
      return False
    else:
      return True
         
  # output key n-grams for a given abstract
  def writeLists(self, out, abs):
    if abs.id not in self.keyTerms:
      print 'WARNING: cannot find', abs.id, 'in list of abstracts'
      return False
    # important unigrams
    for term in self.keyTerms[abs.id].termWeights.keys():
      if self.termIsSpecial(term, abs.id):
        out.write(term+'\n')
        
    # important bigrams    
    for term in self.keyTerms[abs.id].bigramCounts:
      for nextTerm in self.keyTerms[abs.id].bigramCounts[term]:
        if self.bigramIsSpecial(term, nextTerm, abs.id):
          out.write(term+' '+nextTerm+'\n')

    # important trigrams    
    for term1 in self.keyTerms[abs.id].trigramCounts:
      for term2 in self.keyTerms[abs.id].trigramCounts[term1]:
        for term3 in self.keyTerms[abs.id].trigramCounts[term2]:
          if self.trigramIsSpecial(term1, term2, term3, abs.id):
            out.write(term1+' '+term2+' ' +term3+'\n')
   
# labeled sentences to file
def outputAbstracts(absList, filename):
  out = open(filename, 'w')
  out.write("<html><head><title>" + filename + "</title><body>\n<p>")
  for abs in absList:
    out.write('<p><b><u>' + abs.id + ':</u></b></p>\n')
    for sentence in abs.sentences:
      out.write('<br> ')
      for phrase in sentence.phrases:
        out.write(' [')
        for token in phrase.tokens:
          if token.mentionLabel.true != 'other':
            if token.mentionLabel.predicted == 'k':
              out.write(' <span style=\"color:blue\">'+token.text+'</span>')
            else:
              out.write(' <span style=\"color:red\">'+token.text+'</span>')
          else:
            if token.mentionLabel.predicted == 'k':
              out.write(' <s>'+token.text+'</s>')
            else:
              out.write(token.text)
          if token != phrase.tokens[-1]:
            out.write(' ')
          else:
            out.write('] ')
      out.write('\n')
  out.write('</body></html>\n')
  out.close()

  
# perform k-fold crossvalidation
def crossvalidate(filename, nFolds):
  absList = loadAbstractFile(filename)
  cvDataSets = CrossValidationSets(absList, nFolds)
  kwFile = open('keywords.txt', 'w')

  for k in range(0, nFolds):
    nTrainSet = len(cvDataSets.sets[k].train)
    print len(cvDataSets.sets[k].train), len(cvDataSets.sets[k].test)
    # build lists of key terms
    ktLists = KeyTermLists(cvDataSets.sets[k].train, cvDataSets.sets[k].test)
    
    # flag tokens that are identified as key terms
    for abs in cvDataSets.sets[k].test:
      kwFile.write('---'+abs.id+'----\n')
      ktLists.writeLists(kwFile, abs)
      for sentence in abs.sentences:
        for i in range(0, len(sentence.tokens)):
          token1 = sentence.tokens[i]
          # key unigram
          if ktLists.isKeyTerm(token1, abs):
            token1.mentionLabel.predicted = 'k'
          # key bigram
          if i+1 < len(sentence.tokens):
            token2 = sentence.tokens[i+1]
            if ktLists.isKeyBigram(token1, token2, abs):
              token1.mentionLabel.predicted = 'k'
              token2.mentionLabel.predicted = 'k'
              
          # key trigram
          if i+2 < len(sentence.tokens):
            token3 = sentence.tokens[i+2]
            if ktLists.isKeyTrigram(token1, token2, token3, abs):
              token1.mentionLabel.predicted = 'k'
              token2.mentionLabel.predicted = 'k'
              token3.mentionLabel.predicted = 'k'
                

  kwFile.close()
  return absList



############################################################
# if len(sys.argv) < 2:
#   print 'Usage: keywords.py FILE'
#   sys.exit()
# 
# abstractFilename = sys.argv[1]
# absList = crossvalidate(abstractFilename, 10)
# outputAbstracts(absList, 'keywords.html')


