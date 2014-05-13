#!/usr/bin/python
# author: Rodney Summerscales

import random

from basementionfinder import BaseMentionFinder



class RandomMentionFinder(BaseMentionFinder):
  """ Randomly label mentions to achieve a given recall. This finder is for comparison only.
      """
  recall = 1
  randomSeed = 0
  
  def __init__(self, entityTypes, randomSeed, recall=1.0):
    """ Create a finder that labels tokens with a given type if they have this annotation.
        entityType = the mention types to find (e.g. group, outcome)
        recall = desired recall of mention finder [0,1]
    """
    BaseMentionFinder.__init__(self, entityTypes)
    self.recall = recall
    self.randomSeed = randomSeed
    self.finderType = 'random'
              
  def train(self, absList, modelFilename):
    """ (Does nothing. Finder is rule-based, there is nothing to train.) """
    pass    # nothing to train
    
  def test(self, absList, modelFilename):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
    """  
    random.seed(self.randomSeed)
    
    for abs in absList:      
      for sentence in abs.sentences:
        for mType in self.entityTypes:
          # get list of true mentions
          aList = sentence.getAnnotatedMentions(mType, recomputeMentions=True)
          for aMention in aList:
            # randomly select true mentions to label
            r = random.uniform(0, 1)  
            if r <= self.recall:
              # use this mention
              for token in aMention.tokens:
                token.addLabel(mType)
     
  def computeFeatures(self, absList, mode):
    """ (Does nothing. Finder is rule-based, there is nothing to train.) """
    pass    # nothing to train
