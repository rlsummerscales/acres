#!/usr/bin/python
# author: Rodney Summerscales

import math
import os
import sys
import random
import nltk
from nltk.corpus import wordnet as wn
from operator import attrgetter 

from finder import Finder
from entities import Entities


#######################################################################
# Class used to cluster similar mentions
#######################################################################
    
class BaseMentionClusterer(Finder):
  """ Base class for all mention clusterers.
      """
  useDetected = True
  sentenceFilter = None
  
  def __init__(self, entityType, sentenceFilter, useDetected=True):
    """ create a component that can be trained cluster similar mentions 
        of a given type. 
        useDetected = True if detected mentions should be clustered. 
                      Otherwise cluster annotated mentions
        """
    Finder.__init__(self, [entityType])
    self.finderType = 'clusterer'
    self.sentenceFilter = sentenceFilter
    self.useDetected = useDetected    
    
  def train(self, absList, modelFilename):
    """ Train a mention clusterer model given a list of abstracts """
    raise NotImplementedError("Need to implement train()")
     
     
  def test(self, absList, modelFilename, fold=None):
    """ Apply the mention cluster to a given list of abstracts
        using the given model file.
        """
    raise NotImplementedError("Need to implement test()")
     
    
  def computeFeatures(self, absList, mode=''):
   """ compute classifier features for each mention-mention pair in 
        each abstract in a given list of abstracts. """
   raise NotImplementedError("Need to implement computeFeatures()")
  
        
  def computeStats(self, absList, statOut, errorOut):
    """ compute RPF stats for mention clusters.
        write results to output stream. 
        Uses B-cubed algorithm for Recall and Precision."""
        
    nMentions = 0
    pSum = 0
    rSum = 0
    for abstract in absList:
      # build hash of annotated clusters/chains keyed by ID
      errorOut.write('\n---- '+abstract.id+' ----\n')
      trueChainLengths = {}
      entityList = abstract.annotatedEntities.getList(self.entityTypes[0])
      errorOut.write('True chains:\n')
      for entityTemplate in entityList:
        if len(entityTemplate.getAnnotatedId()) > 0:
          trueChain = entityTemplate.getMentionChain()
          trueChainLengths[entityTemplate.getAnnotatedId(checkEntireCluster=False)] = len(trueChain)
          for m in trueChain:
#            errorOut.write(m.name+':'+m.getAnnotatedId(checkEntireCluster=False) +'\n')
            errorOut.write('%s %s:%s, matchedMention=%s \n'%(m.name, m.mention, m.getAnnotatedId(checkEntireCluster=False), m.mention.matchedMention))

          errorOut.write('----\n')
        else:
          print abstract.id, entityTemplate.name, 'is missing an ID'
          
      # compute Recall and precision for each detected chain/cluster
      entityList = abstract.entities.getList(self.entityTypes[0])
      errorOut.write('\nHypothesis chains:\n')
      for entityTemplate in entityList:
        detectedChain = entityTemplate.getMentionChain()
        
        rootMention = entityTemplate.rootMention()
        errorOut.write('[Canonical name: '+rootMention.getCanonicalName()+']\n')
        
        for m in detectedChain:
          errorOut.write('%s %s:%s, matchedMention=%s \n'%(m.name, m.mention, m.getAnnotatedId(checkEntireCluster=False), m.mention.matchedMention))
#          errorOut.write(m.name+':'+m.getAnnotatedId(checkEntireCluster=False) +'\n')
        errorOut.write('----\n')

        nMentionsInChain = len(detectedChain)
        for mTemplate in detectedChain:
          nMentions += 1
          if len(mTemplate.getAnnotatedId(checkEntireCluster=False)) == 0:
            # mention is a false positive, it does not belong to any chain
            pSum += 1.0/nMentionsInChain
            rSum += 1
          else:
            if mTemplate.getAnnotatedId(checkEntireCluster=False) not in trueChainLengths:
              print abstract.id, 'template with id =',mTemplate.getAnnotatedId(checkEntireCluster=False), 'not in a true chain'
              break
            nMentionsInTrueChain = trueChainLengths[mTemplate.getAnnotatedId(checkEntireCluster=False)]
            nCorrectInDetectedChain = 0
            annotatedMatches = set([])
            # count the number of mentions in the detected chain that
            # should be in the same chain as this mention
            for m in detectedChain:
              if mTemplate.getAnnotatedId(checkEntireCluster=False) == m.getAnnotatedId(checkEntireCluster=False) \
                and m.mention.matchedMention not in annotatedMatches:
                nCorrectInDetectedChain += 1
                annotatedMatches.add(m.mention.matchedMention)
#               else:
#                 print abstract.id, 'Two mentions do not belong in same chain',
#                 print mTemplate, m.getAnnotatedId()
            
            if nCorrectInDetectedChain > nMentionsInTrueChain:
              print abstract.id, 'id=',mTemplate.getAnnotatedId(checkEntireCluster=False), 
              print 'detected chain=', nCorrectInDetectedChain,
              print 'true chain=', nMentionsInTrueChain
              nCorrectInDetectedChain = nMentionsInTrueChain
            
#             if nCorrectInDetectedChain != nMentionsInChain:
#               print abstract.id, 'id=',mTemplate.getAnnotatedId(), 
#               print 'detected chain=', nCorrectInDetectedChain,
#               print 'true chain=', nMentionsInTrueChain
                
            pSum += float(nCorrectInDetectedChain) / nMentionsInChain
            rSum += float(nCorrectInDetectedChain) / nMentionsInTrueChain
     
    if nMentions == 0:
      print 'No mentions???'
      return 
              
    precision = pSum/nMentions
    recall = rSum/nMentions        
    fscore = 2*(recall*precision)/(recall + precision)
    
    sys.stdout.write('Recall\tPrecision\tF-score\n')
    sys.stdout.write('%.3f\t ' % recall + '%.3f\t ' % precision + '%.3f' % fscore+'\n')
#     statOut.write(self.entityTypesString+'\n')
#     statOut.write('Recall\tPrecision\tF-score\n')
#     statOut.write('%.3f\t ' % recall + '%.3f\t ' % precision + '%.3f' % fscore+'\n')
    statOut.addStats('MC - '+self.entityTypesString, [['R', recall], ['P', precision], ['F',fscore]])  
 


  
  def similarity(self, wSet1, wSet2, idf):
    """ find similarity (ignoring function words, etc) between two word sets
    """  
    if len(wSet1) == 0 or len(wSet2) == 0:
      return 0.0
    else:
      defaultIDF = idf['unknownToken']
      intersection = wSet1.intersection(wSet2)
#      intersection = self.synonymIntersection(wSet1, wSet2, idf)
      if len(intersection) == 0:
        return 0
      sum1 = 0
      sum2 = 0
      intersectionSum = 0
      for word in wSet1:
        sum1 += (idf.get(word, defaultIDF))**2
      for word in wSet2:
        sum2 +=  (idf.get(word, defaultIDF))**2
      for word in intersection:
        intersectionSum += (idf.get(word, defaultIDF))**2
                          
      if sum1 == 0 or sum2 == 0:
        return 0.0
      else:
        return intersectionSum/(math.sqrt(sum1) * math.sqrt(sum2))
  

  def getSynonyms(self, wordSet):
    """ generate a set of synonyms for each word in a set of words """
    synonyms = {}
    for w in wordSet:
     # find synonyms
     synsets = wn.synsets(w, pos=wn.NOUN)
     if len(synsets) > 0: 
       # there are noun senses for this word, get synonyms
       synonyms[w] = set([synset.name for synset in synsets])
    
    return synonyms

  def synonymIntersection(self, wSet1, wSet2, idf):
    """ return the intersection of two sets using synsets. """
    intersection = wSet1.intersection(wSet2)
    w1 = wSet1 - intersection
    w2 = wSet2 - intersection
    if len(intersection) == 0:
      return set([])

    synonyms1 = self.getSynonyms(w1)
    synonyms2 = self.getSynonyms(w2)
    defaultIDF = idf['unknownToken']
    
    while len(w1) > 0:
      word1 = w1.pop()
      if word1 not in synonyms1:
        continue   # no synonyms for this word
  
      for word2 in w2:
        if word2 not in synonyms2:
          continue  # no synonyms for this word
        sharedSynsets = synonyms1[word1].intersection(synonyms2[word2])
        if len(sharedSynsets) > 0:
          # the two have at least one synset in common, consider them synonyms
          w2.remove(word2)
          if idf.get(word1, defaultIDF) > idf.get(word2, defaultIDF):
            intersection.add(word1)
          else:
            intersection.add(word2)
          break
      
    return intersection
    

  def synSimilarity(self, wSet1, wSet2):
    """ similarity measure that includes synonyms """  
    nW1 = len(wSet1)
    nW2 = len(wSet2)
    if nW1 == 0 or nW2 == 0:
      return 0.0
    synonyms1 = self.getSynonyms(wSet1)
    synonyms2 = self.getSynonyms(wSet2)
    
    # easy bit: find the number of identical words in each mention
    intersection = wSet1.intersection(wSet2)
    # now remove these words and look for synonyms between those left
    w1 = wSet1 - intersection
    w2 = wSet2 - intersection
    while len(w1) > 0:
      word1 = w1.pop()
      if word1 not in synonyms1:
        continue   # no synonyms for this word
  
      for word2 in w2:
        if word2 not in synonyms2:
          continue  # no synonyms for this word
        sharedSynsets = synonyms1[word1].intersection(synonyms2[word2])
        if len(sharedSynsets) > 0:
          # the two have at least one synset in common, consider them synonyms
          w2.remove(word2)
          intersection.add(word1)
  
          break
    return float(2*len(intersection)) / (nW1 + nW2)






