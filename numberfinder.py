import sys
import os.path
import nltk
from nltk.corpus import stopwords
from finder import EntityStats
from mentionfinder import MentionFinder
      
######################################################################
# Experimental mention finder
######################################################################

class NumberFinder(MentionFinder):
  """ Used for training/testing a classifier to find mentions 
      in a list of abstracts.
      """  
  def __init__(self, entityTypes, tokenClassifier, labelFeatures=[], useReport=True):
    """ Create a new mention finder to find a given list of mention types.
        entityTypes = list of mention types to find (e.g. group, outcome)
    """
    MentionFinder.__init__(self, entityTypes, tokenClassifier, labelFeatures, useReport, \
                           tokenFilter=self.isImportantNumber)
    self.finderType = 'number'
       
#  def readLabelsAndAssign(self, absList, labeledFilename):
#    """ read the file containing labels assigned by the classifier and 
#        assign the labels to the appropriate tokens """
#
#    # store assigned labels in abstract list
#    # read labeled phrase file
#    labels = self.tokenClassifier.readLabelFile(labeledFilename)
#    i = 0
#    for abs in absList:
#      for sentence in abs.sentences:
#        for token in sentence.tokens:
#          if self.isImportantNumber(token):
#            if i >= len(labels):
#              raise StandardError("not all tokens are labeled")
#            if labels[i] != 'other' and self.safeToLabelNumber(token, labels[i]):
#              token.addLabel(labels[i])
##            elif token.isPercentage():
##              token.addLabel('eventrate')
#            i += 1
                
  def isImportantNumber(self, token):
    """ return true if the token is an integer that we want to label """
    if token.isImportantNumber():
      for label in self.entityTypes:
        if self.safeToLabelNumber(token, label):
          return True
    return False
  
  def computeStats(self, absList, statOut=None, errorOut=None):
    """ compute RPF stats for detected quantities in a list of abstracts.
        write results to output stream. 
        
        write final RPF stats to statOut
        write TP/FP/FN to errorOut
        """      
    stats = EntityStats(self.entityTypes)
    for abs in absList:
      errorOut.write('---'+abs.id+'---\n')
      for sentence in abs.sentences:
        # decide if should output sentence
        printedSentence = False
        # count correct and incorrect labelings
        for eType in self.entityTypes:
          for token in sentence:
            if self.isImportantNumber(token) == True:
              if token.hasLabel(eType) and token.hasAnnotation(eType):
                stats.irstats[eType].incTP()
                errorOut.write('+TP: ' + token.text + ' ('+eType+')\n')
              elif token.hasLabel(eType) == True:
                stats.irstats[eType].incFP()
                errorOut.write('-FP: ' + token.text + ' ('+eType+')\n')
              elif token.hasAnnotation(eType) == True:
                stats.irstats[eType].incFN()
                errorOut.write('-FN: ' + token.text + ' ('+eType+')\n')
  
    stats.printStats()
#    stats.writeStats(statOut)
    if statOut != None:
      stats.saveStats(statOut, keyPrefix='NF - ')
          
    return stats
     
        
        
  def computeFeatures(self, absList, mode):
    """ compute features for each token in each abstract in a given
        list of abstracts.
    """
    for abstract in absList:
      registryWords = self.registryWordSets(abstract)

      for sentence in abstract.sentences:
        sFeatures = self.sentenceFeatures(sentence)
          
        # build list of numbers that should be classified 
        parenDepth = 0
        for token in sentence:
          if self.isImportantNumber(token):
            # compute features for this number 
            token.features = {}
  
            # compute features
            token.features['sentence'] = sFeatures
            token.features['token'] = self.tokenFeatures(token)
            token.features['syntactic'] = self.syntacticContextFeatures(token, mode, \
                                                    parenDepth, registryWords)
            token.features['tContext'] = self.tokenContextFeatures(token, mode, 3, \
                                                    registryWords)
            token.features['semantic'] = self.semanticFeatures(token, mode)

            token.features['pattern'] = self.numberPatternFeatures(token) # redundant, handled by semantic
          else:
            # not a number, check if we are entering or leaving a parenthetical
            if token.text == '-LRB-':
              parenDepth += 1
            elif token.text == '-RRB-':
              parenDepth -= 1

                  

