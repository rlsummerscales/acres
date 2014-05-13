#!/usr/bin/python
# base class for an object for detecting mentions (e.g. group, outcome)
# author: Rodney Summerscales

import sys
import os.path
from finder import Finder
from finder import EntityStats
      
######################################################################
# Mention finder base class
######################################################################


class BaseMentionFinder(Finder):
  """ Used for training/testing a classifier to find mentions 
      in a list of abstracts.
      (NOTE: This is the base class. The actual mention finders should
      be derived from this class.
      """  
  tokenClassifier = None
  
  def __init__(self, entityTypes, tokenClassifier):
    """ Create a new mention finder to find a given list of mention types.
        entityTypes = list of mention types (e.g. group, outcome) to find
        """
    Finder.__init__(self, entityTypes)
    self.tokenClassifier = tokenClassifier
    if self.tokenClassifier != None:
      self.finderType = 'mention.'+self.tokenClassifier.classifierType
    else:
      self.finderType = 'mention'
    
  def computeFeatures(self, absList):
    """ compute classifier features for each token in each abstract in a
        given list of abstracts. """
    raise NotImplementedError("Need to implement computeFeatures()")
    
  def train(self, absList, modelfilename):
    """ Train a mention finder model given a list of abstracts """
    raise NotImplementedError("Need to implement train()")
    
  def test(self, absList, modelfilename, fold=None):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
        """
    raise NotImplementedError("Need to implement test()")
    
    
    
  def computeStats(self, absList, statOut=None, errorOut=None):
    """ compute RPF stats for detected mentions in a list of abstracts.
        write results to output stream.
        
        write final RPF stats to statOut
        write TP/FP/FN to errorOut
        """
      
    stats = EntityStats(self.entityTypes)
    for abs in absList:
      errorOut.write('---'+abs.id+'---\n')      
      
      # identify ALL annotated mentions, even in sentences we are not focused on
#      for sentence in abs.allSentences():
#        for mType in self.entityTypes:
#          aList = sentence.getAnnotatedMentions(mType, recomputeMentions=True)
#        
#      for sentence in abs.sentences:
#        for mType in self.entityTypes:
#          self.compareAnnotatedAndDetected(sentence, mType, \
#                               stats.irstats[mType], errorOut)


      for sentence in abs.allSentences():
        for mType in self.entityTypes:
          if sentence in abs.sentences:
            self.compareAnnotatedAndDetected(sentence, mType, \
                               stats.irstats[mType], errorOut)
          else:          
            aList = sentence.getAnnotatedMentions(mType, recomputeMentions=True)
        

    stats.printStats()
    if statOut != None:
      stats.saveStats(statOut, keyPrefix='MF - ')
    
    return stats
  
  def write(self, out, message):
    """ write a message to a given output stream """
    if out != None:
      out.write(message)
  
  def compareAnnotatedAndDetected(self, sentence, mType, irStats, errorOut=None):
    """ Compute lists of detected and annotated mentions and compare them.
        count number of true positives, false positives, and false negatives.
        """
    aList = sentence.getAnnotatedMentions(mType, recomputeMentions=True)
    dList = sentence.getDetectedMentions(mType, recomputeMentions=True)      
    if len(aList) == 0 and len(dList) == 0:
      return
    self.compareMentionLists(dList, aList, mType, irStats, errorOut)
    
  def compareMentionLists(self, dList, aList, mType, irStats, errorOut=None):
    """ compare list of annotated mentions with list of detected mentions.
        count number of true positives, false positives, and false negatives.
        """
    # build lists of overlapping mentions for annotated and detected mentions in this sentence
    potentialMatches = {}
    for aMention in aList:
      potentialMatches[aMention] = []
    for dMention in dList:
      potentialMatches[dMention] = []
      for aMention in aList:
        if dMention.countOverlapTokens(aMention) > 0:
          potentialMatches[dMention].append(aMention)
          potentialMatches[aMention].append(dMention)
  
    # check matches for each detected template
    for dMention in dList:
      aMentionList = potentialMatches[dMention]
      if len(aMentionList) == 1 and dMention.matchAnnotated(aMentionList[0]):
        # there is only one annotated mention that matches this detected one
        # this is either a TP or a DUPLICATE
        annotatedMention = aMentionList[0]
        if len(potentialMatches[annotatedMention]) == 1:
          # this detected mention matches only ONE annotated one, count as TP
          # OTHERWISE, deal with it when we process annotated mentions
          dMention.matchedMention = annotatedMention
          annotatedMention.matchedMention = dMention
#          self.write(errorOut, '+TP: '+dMention.text+' == '+annotatedMention.text+' ('+mType+')\n')
          self.write(errorOut, '+TP: %s == %s %s (%s)\n'%(dMention.text, annotatedMention.text, annotatedMention, mType))

          irStats.incTP() 
      else:
        # this detected mention overlaps multiple annotated mentions. 
        # OR it does not match any annotated mention. either way, discard it.
        # count it as a FP
        self.write(errorOut, '-FP: '+dMention.text+' ('+mType+')\n')
        irStats.incFP()
        for aMention in aMentionList:
          potentialMatches[aMention].remove(dMention)
          self.write(errorOut, 'DETECTED MENTION OVERLAPS '+aMention.text+'\n')
        potentialMatches[dMention] = []

    # check matches for each annotated mention    
    for annotatedMention in aList:
      dMatches = potentialMatches[annotatedMention]
      if len(dMatches) == 0:
        # annotated mention was unmatched, count as FN
        irStats.incFN()
        self.write(errorOut, '-FN: '+annotatedMention.text+' ('+mType+')\n')
      elif len(dMatches) > 1:
        # annotated mention overlapped multiple detected ones
        # check each one to see if it counts as a match
        # If more than one does, count the best match as a TP
        # and the rest as duplicates.
        bestMatches = []
        for dMention in dMatches:
          if dMention.matchAnnotated(annotatedMention):
            overlap = dMention.countOverlapTokens(annotatedMention)
            bestMatches.append([overlap, dMention])
            dMention.matchedMention = annotatedMention
          else:
            # detected mention did not sufficiently match, count as FP
            self.write(errorOut, '-FP: '+dMention.text+' ('+mType+')\n')
            irStats.incFP()

        if len(bestMatches) > 0:
          # count best match
          bestMatches.sort()
          dMention = bestMatches[-1][1]
          dMention.matchedMention = annotatedMention
          annotatedMention.matchedMention = dMention          
          self.write(errorOut, '+TP: '+dMention.text+' == '+annotatedMention.text+' ('+mType+')\n')        
          irStats.incTP() 
          # count duplicates
          for i in range(0, len(bestMatches)-1):
            irStats.incDuplicates()
            dMention = bestMatches[i][1]          
            self.write(errorOut, 'ANNOTATED MENTION ALSO MATCHES ')
            self.write(errorOut, dMention.text+'\n')
            dMention.matchedMention = annotatedMention
        else:
          # there are no valid matches
          irStats.incFN()
          self.write(errorOut, '-FN: '+annotatedMention.text+' ('+mType+')\n')
              
        


