#!/usr/bin/python
# author: Rodney Summerscales
# split up a given list of items for the purpose of k-fold crossvalidation

import random

##############################################################
# keep a list of items for training and one for testing
##############################################################

class DataSets:
  test = []     # list of items in test set
  train = []    # list of items in training set

  def __init__(self, train, test):
    self.test = test 
    self.train = train

#######################################################################
# maintain k testing/training sets of items for k-fold crossvalidation
#######################################################################

class CrossValidationSets:
  __sets = []     # list of testing/training sets for k-fold crossvalidation
  __index = 0     # current index into list of abstracts (used by iterator)
  randomSeed = 42
  
  def __init__(self, list, nFolds, randomSeed=42):
    self.__sets = []
    self._index = 0
    
    n = len(list)
    nLeftToTest = n

    self.randomSeed = randomSeed
    random.seed(self.randomSeed)
    random.shuffle(list)
    startIdx = 0
    dataSets = []

    for k in range(0, nFolds):
      testSet = []
      trainSet = []
      testSetSize = int(round(float(nLeftToTest)/(nFolds-k)))
      nLeftToTest = nLeftToTest - testSetSize
      endIdx = startIdx + testSetSize
      for i in range(0, n):
        if startIdx <= i and i < endIdx:
          testSet.append(list[i])
        else:
          trainSet.append(list[i])

      ds = DataSets(trainSet, testSet)
      self.__sets.append(ds)
      startIdx = endIdx
    
#    self.__sets.reverse()
      
  # implement len() method
  def __len__(self):
    return len(self.__sets)
  
  # routines needed for implementing the iterator      
  def __iter__(self):
    self.__index = 0
    return self
 
  def __getitem__(self, index):
    return self.__sets[index]
   
  def next(self):
    if self.__index == len(self.__sets):
      raise StopIteration
    self.__index = self.__index + 1
    return self.__sets[self.__index-1]
   