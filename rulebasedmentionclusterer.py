#!/usr/bin/python
# author: Rodney Summerscales

import math
import os
import sys
import random
import nltk
from nltk.corpus import wordnet as wn
from operator import attrgetter 

from baseclusterer import BaseMentionClusterer
from entities import Entities


#######################################################################
# Class used to cluster similar mentions
#######################################################################
    
class RuleBasedMentionClusterer(BaseMentionClusterer):
  """ Cluster mentions that are exact matches of each other.
      """
  
  def __init__(self, entityType, sentenceFilter):
    """ create a component that can be trained cluster similar mentions 
        of a given type. 
        threshold = probability threshold for two mentions refering to same entity
                    if two mention have a match probability greater than this
                    threshold, consider them to refer to same entity
                    (default is 0.5)
        useDetected = True if detected mentions should be clustered. 
                      Otherwise cluster annotated mentions
        """
    BaseMentionClusterer.__init__(self, entityType, sentenceFilter)
    self.finderType = 'heuristic-cluster'
    
  def train(self, absList, modelFilename):
    """ Train a mention clusterer model given a list of abstracts """
    for abstract in absList:
      if abstract.annotatedEntities == None:
        abstract.annotatedEntities = Entities(abstract)
      abstract.annotatedEntities.createTrueEntities(self.entityTypes[0], self.sentenceFilter)
#      print 'train:', len(abstract.annotatedEntities.getList('group')), len(abstract.annotatedEntities.getList('outcome'))
       
     
  def test(self, absList, modelFilename, fold=None):
    """ Cluster mentions using annotated mention ids.
        """      
    for abs in absList:
      self.clusterMentions(abs)
      
      
  def computeFeatures(self, absList, mode=''):
    """ compute classifier features for each mention-mention pair in 
        each abstract in a given list of abstracts. """
    pass    

  def clusterMentions(self, abstract):
    """ cluster mentions that refer to same entity in a given abstract. 
        create list of entities using hierarchical aglomerative clustering 
        """
    # cluster DETECTED mentions 
    if abstract.entities == None:
      abstract.entities = Entities(abstract)
    abstract.entities.createEntities(self.entityTypes[0], self.sentenceFilter,\
                                     useDetected=True, useIds=False)
    if abstract.annotatedEntities == None:
      abstract.annotatedEntities = Entities(abstract)
    abstract.annotatedEntities.createTrueEntities(self.entityTypes[0], self.sentenceFilter)
   
    # discard groups that are likely to be false positives                         
#    if self.entityTypes[0] == 'group':
#      gList = self.filterGroupClusters(abstract.entities.lists[self.entityTypes[0]])
#      abstract.entities.lists[self.entityTypes[0]] = gList
      
    # assign ids to each of the mention clusters
    currentId = 0
    for mTemplate in abstract.entities.lists[self.entityTypes[0]]:
      mTemplate.setId(str(currentId))
      currentId += 1    


  
        

