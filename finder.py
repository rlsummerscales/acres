#!/usr/bin/python
# base class for an object that identifies mentions and quantities
# author: Rodney Summerscales

import sys
import os.path
import nltk
from nltk.corpus import stopwords
from irstats import IRstats

######################################################################
# class for recording RPF statistics for an entity finder
######################################################################

class EntityStats:
  """ Used to calculate recall, precision, f-score for mention finder """
  irstats = {}
  entityTypes = []     # list of entity types found by an entity finder
  
  def __init__(self, entityTypes):
    """ start computing RPF statistics for new set of abstracts """
    self.irstats = {}
    self.entityTypes = entityTypes
    for mType in self.entityTypes:
      self.irstats[mType] = IRstats()

  def add(self, ms):
    """ add tp, fp, fn counts from an other mention stat object """
    for mType in self.entityTypes:
      self.irstats[mType].tp = self.irstats[mType].tp + ms.irstats[mType].tp
      self.irstats[mType].fp = self.irstats[mType].fp + ms.irstats[mType].fp
      self.irstats[mType].fn = self.irstats[mType].fn + ms.irstats[mType].fn

  def printStats(self):
    """ Output the RPF statistics to screen """
    print 'TP', 'FP', 'FN', 'R', 'P', 'F'
    for mType in self.entityTypes:
      print mType,' ',
      self.irstats[mType].displayrpf()

  def saveStats(self, statList, keyPrefix=''):
    """ Add these stats to a given list of stats.
        keyPrefix is prefix string attached to the beginning of the entity type
          which is used as the key into the given has of stats. """
    for mType in self.entityTypes:
      statList.addIRstats(keyPrefix+mType, self.irstats[mType])
    
  def writeStats(self, out):
    """ write RPF stats to given output stream """
    out.write('\tTP  FP  FN  R  P  F\n')
    for mType in self.entityTypes:
      out.write(mType+'\t')
      self.irstats[mType].writerpf(out)
      
######################################################################
# Mention finder base class
######################################################################

class Finder:
  """ Used for training/testing a classifier to find mentions 
      in a list of abstracts.
      (NOTE: This is the base class. The actual mention finders should
      be derived from this class.
      """
  finderType = 'basefinder'    
  entityTypes = []   # list of types mention finder will look for
  entityTypesString = ''
  
  
  def __init__(self, entityTypes):
    """ Create a new mention finder to find a given list of mention types.
        entityTypes = list of mention types (e.g. group, outcome) to find
        """
    self.finderType = 'basefinder'
    self.entityTypes = entityTypes
    self.entityTypesString = '-'.join(self.entityTypes)

  def getFoldString(self, foldIndex):
    """ return string with fold index formatted for filenames """
    if foldIndex != None:
      return '.%d' % foldIndex
    else:
      return ''

  def computeFeatures(self, absList, mode=''):
    """ compute classifier features for each token in each abstract in a
        given list of abstracts. 

        mode = 'test', 'train', or 'crossval'
        
    """
    raise NotImplementedError("Need to implement computeFeatures()")
    
  def train(self, absList, modelfilename):
    """ Train a mention finder model given a list of abstracts """
    raise NotImplementedError("Need to implement train()")
    
  def test(self, absList, modelfilename, fold=None):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
        """
    raise NotImplementedError("Need to implement test()")
    
  def crossvalidate(self, absList, modelPath):
    """ Apply mention finder to list of abstracts using k-fold 
        crossvalidation. The crossvalidation sets should be defined
        in the AbstractList object (absList). 
        """    
    if modelPath[-1] != '/':
      modelPath = modelPath + '/'
    k = 0
    for dataSet in absList.cvSets:
      print k+1, len(dataSet.train), len(dataSet.test)
      modelFilename = modelPath+self.entityTypesString+'.'+str(k)+'.model'
      k += 1
      # train model
      self.train(dataSet.train, modelFilename)
      # apply to test set
      self.test(dataSet.test, modelFilename)
      print '-----------------'

  def computeStats(self, absList, out=None, errorOut=None):
    """ compute RPF stats for detected mentions in a list of abstracts.
        write results to output stream. """
    raise NotImplementedError("Need to implement computeStats()")
