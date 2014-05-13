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
from baseclusterer import BaseMentionClusterer
from entities import Entities

#############################################
# feature vectors used when clustering mention
#############################################
class FeatureVector:
  """ Stores list of features for a pair of mentions.
      features are used to determine if two mentions coref
  """
  mention1 = ""         # first mention template
  mention2 = ""         # second mention template
  label = ""       # class label for fv
  features = None    # list of features
  prob = 0.0       # probability that both mentions refer to same entity
  
  def __init__(self, mention1, mention2, label):
    self.mention1 = mention1
    self.mention2 = mention2
    self.label = label
    self.features = set([])
    self.prob = 0.0

  def add(self, featureName):
    """ add a new feature to the current list of features """
    self.features.add(featureName)

  def write(self, out):
    """
      write feature vector to a file formated for megam 
      <label> <feature1> ... <featureN>
      """
    out.write(self.label)
    for f in self.features:
        out.write(' ' + f)
    out.write('\n')  



#######################################################################
# Class used to cluster similar mentions
#######################################################################
    
class MentionClusterer(BaseMentionClusterer):
  """ Used for training/testing a classifier to identify and merge 
      similar mentions into clusters.
      """
  useDetected = True
  matchThreshold = 0.5
  
  
  
  def __init__(self, entityType, sentenceFilter, threshold=0.5, useDetected=True):
    """ create a component that can be trained cluster similar mentions 
        of a given type. 
        threshold = probability threshold for two mentions refering to same entity
                    if two mention have a match probability greater than this
                    threshold, consider them to refer to same entity
                    (default is 0.5)
        useDetected = True if detected mentions should be clustered. 
                      Otherwise cluster annotated mentions
        """
    BaseMentionClusterer.__init__(self, entityType, sentenceFilter, useDetected)
    self.matchThreshold = threshold
    
    
    
  def train(self, absList, modelFilename):
    """ Train a mention clusterer model given a list of abstracts """
    trainFilename = 'features.'+self.entityTypesString+'.cluster.train.txt'

    self.writeFeatureFile(absList, trainFilename, forTraining=True)
    cmd = 'bin/megam.opt -quiet -tune -fvals binary ' + trainFilename + ' > ' \
      + modelFilename
    cmd = 'bin/megam.opt -quiet -tune binary ' + trainFilename + ' > ' \
      + modelFilename

    os.system(cmd)
     
     
     
  def test(self, absList, modelFilename, fold=None):
    """ Apply the mention-quantity associator to a given list of abstracts
        using the given model file.
        """
    testFilename = 'features.'+self.entityTypesString+'.cluster.test.txt'
    resultFilename = 'cluster.results.txt'

    self.writeFeatureFile(absList, testFilename, forTraining=False)
    cmd = 'bin/megam.opt -quiet  -fvals -predict  ' + modelFilename + ' binary ' \
       + testFilename + ' > ' + resultFilename 
    cmd = 'bin/megam.opt -quiet  -predict  ' + modelFilename + ' binary ' \
       + testFilename + ' > ' + resultFilename 

    os.system(cmd)
    
    # get probabilites from result file
    resultLines = open(resultFilename, 'r').readlines()
    featureVectors = self.getFeatureVectors(absList, forTraining=False)
    i = 0    # current feature vector
    for line in resultLines:
      parsedLine = line.strip().split()
      prob = float(parsedLine[-1])
      featureVectors[i].prob = prob
      i = i + 1
      
    # merge the mentions that are considered to be similar
    for abs in absList:
      self.clusterMentions(abs)
      
      
      
  def writeFeatureFile(self, absList, featureFilename, forTraining):
    """ write features to a file that can be read by megam  """
    featureVectors = self.getFeatureVectors(absList, forTraining)
    out = open(featureFilename, 'w')
    for fv in featureVectors:
      fv.write(out)



  def getFeatureVectors(self, absList, forTraining):
    """ return list of features vectors to use for training/testing 
        
        absList = list of abstracts to get features vectors for
        forTraining = True if feature vectors will be used for training, 
                      False if used for testing. 
                      If used for training, use annotated mentions."""
    list = []
    for abs in absList:
      if forTraining == True:
        # use annotated mentions
        entities = abs.annotatedEntities
      else:
        # use detected mentions
        entities = abs.entities
      for fv in entities.featureVectors:
        list.append(fv)          
    return list    


  def clusterMentions(self, abstract):
    """ cluster mentions that refer to same entity in a given abstract. 
        create list of entities using hierarchical aglomerative clustering 
        """
    # cluster DETECTED mentions    
    entities = abstract.entities
    if len(entities.featureVectors) == 0:
      return              # nothing to cluster     
      
    # consider mention pairs with the highest probability of coreferring
#    if self.entityTypes[0] != 'group':

    fvList = sorted(entities.featureVectors, key=attrgetter('prob'), reverse=True)
    for fv in fvList:
      if self.entityTypes[0] == 'group' and len(entities.lists['group']) <= 2:
        break   # stop when we reach two groups
        
      if fv.prob > self.matchThreshold \
        and fv.mention1.rootMention() != fv.mention2.rootMention(): 
        entities.mergeTemplates(fv.mention1, fv.mention2, entities.lists[self.entityTypes[0]])    

    # discard groups that are likely to be false positives     
#    if self.entityTypes[0] == 'group':
#      gList = self.filterGroupClusters(abstract.entities.lists[self.entityTypes[0]])
#      abstract.entities.lists[self.entityTypes[0]] = gList
   
    # assign ids to each of the mention clusters
    currentId = 0
    for mTemplate in entities.lists[self.entityTypes[0]]:
      mTemplate.setId(str(currentId))
      currentId += 1    



    
  def computeFeatures(self, absList, mode=''):
    """ compute classifier features for each mention-mention pair in 
        each abstract in a given list of abstracts. """
    for abs in absList:
      if abs.entities == None:
        abs.entities = Entities(abs)
      if abs.annotatedEntities == None:
        abs.annotatedEntities = Entities(abs)

      # compute idf from current abstract list (ignore current one)
      # TODO: Eventually replace this with idf stats computed from a 
      #       a separate corpus
      documentCounts = {}
      for i in range(0, len(absList)):
        abs2 = absList[i]
        if abs2 != abs:
          for lemma in abs2.getLemmaSet():
            documentCounts[lemma] = 1 + documentCounts.get(lemma, 0)
      idf = {}
      nAbs = float(len(absList) - 1)
      for lemma, counts in documentCounts.items():
        idf[lemma] = math.log(nAbs/counts)
          
      idf['unknownToken'] = math.log(nAbs)
      
      abs.entities.createEntities(self.entityTypes[0], self.sentenceFilter,\
                                  useDetected=self.useDetected)
      abs.annotatedEntities.createTrueEntities(self.entityTypes[0], self.sentenceFilter)
      
      self.computePairFeatures(abs.entities, idf)
      self.computePairFeatures(abs.annotatedEntities, idf)

  def getMentionList(self, entities):
    """ return list of mentions from a given collection of entities """
    entityList = entities.getList(self.entityTypes[0])
    mentionList = []
    for mTemplate in entityList:
      mentionList += mTemplate.getMentionChain()
    return mentionList

  def computePairFeatures(self, entities, idf, mode=''):
    """ compute features for each possible pairing of mentions in a given
        set of entities
    """
    mentionList = self.getMentionList(entities)
    entities.featureVectors = []
    for mTemplate1 in mentionList:
      for mTemplate2 in mentionList:
        if mTemplate1 != mTemplate2:
          if len(mTemplate1.getAnnotatedId()) > 0 \
             and mTemplate1.getAnnotatedId() == mTemplate2.getAnnotatedId():
            label = "1"   # mentions refer to same entity
          else:
            label = "0"   
            
          fv = FeatureVector(mTemplate1, mTemplate2, label)
          
          m1Words = mTemplate1.mention.interestingLemmas()
          m2Words = mTemplate2.mention.interestingLemmas()
          # find similarity
          s = self.similarity(m1Words, m2Words, idf)
#          fv.add('SIM ' + "%3.2f" % s)
          fv.add('SIM_' + str(int(s*3)))

          if s > 0.99 and fv.label == '0':  # the two mentions are identical
            fv.label = '1'                 # consider this an annotation error

          # feature for common control phrase
          if self.entityTypes[0] == 'group':
            if (mTemplate1.isControl() and mTemplate2.isControl()) \
               or (mTemplate1.isExperiment() and mTemplate2.isExperiment()):
  #            fv.add('CONTROL 1.0')
              fv.add('SAME_GROUP_ROLE')
              fv.label = '1'
            elif (mTemplate1.isControl() and mTemplate2.isExperiment()) \
               or (mTemplate1.isExperiment() and mTemplate2.isControl()):
              fv.add('DIFF_GROUP_ROLE')
              fv.label = '0'
            # check if the groups have sizes
#             g1Size = mTemplate1.getSize()
#             g2Size = mTemplate2.getSize()
#             if g1Size > 0 and g2Size > 0:
#               fv.add('BOTH_HAVE_OWN_SIZE')
#             elif g1Size > 0 or g2Size > 0:
#               fv.add('ONLY_ONE_HAS_SIZE') 
    
          if len(m1Words-m2Words) == 0 or len(m2Words-m1Words) == 0:
            fv.add('SUBSET')
            
          # look for shared UMLS codes
          codes1 = mTemplate1.umlsCodes
          codes2 = mTemplate2.umlsCodes
          sharedCodes = codes1.intersection(codes2)
          if len(codes1) > 0 or len(codes2) > 0:
            codeSimilarity = float(2*len(sharedCodes))/(len(codes1)+len(codes2)) 
            fv.add('UMLS_'+str(int(codeSimilarity*3)))
          else:
            fv.add('NO_UMLS')
            
            
          # find synonym similarity
#           s = self.synSimilarity(m1Words, m2Words)
# #          fv.add('SYNSIM ' + "%3.2f" % s)
#           fv.add('SYNSIM_' + str(int(s*3)))
          
          # find various word similarities
          negWords = mTemplate1.mention.tokens[0].negationWordSet
#                   ['or'], ['and', 'plus']
          nNegWords1 = len(m1Words.intersection(negWords))         
          nNegWords2 = len(m2Words.intersection(negWords))         
          if nNegWords1 != nNegWords2:
            fv.add('DIFFERENT_POLARITY')
            
          # in same sentence?
          sentence1 = mTemplate1.getSentence()
          sentence2 = mTemplate2.getSentence()
          if sentence1 == sentence2:
            fv.add('SAME_SENTENCE')            
            
          entities.featureVectors.append(fv)           
          
  
        

