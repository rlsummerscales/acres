#!/usr/bin/python
# author: Rodney Summerscales

class TokenLabel:
  """ label and it's probilities assigned to a token by a classifier """
  label=None
  prob=0.0
  sequenceProb=0.0
  
  def __init__(self, label):
    """ create new label with given name and probabilities of 1.0 """
    self.label = label
    self.prob = 1.0
    self.sequenceProb = 1.0

class BaseTokenClassifier:
  """ Base class for classifier object that labels tokens in a sentence.
      (NOTE: This is the base class. The actual mention finders should
      be derived from this class.
      """  
  classifierType = None
  topK = 1
  
  def __init__(self, classifierType, topK=1):
    self.classifierType = classifierType
    self.topK = topK
          
  def train(self, absList, modelfilename, entityTypes):
    """ Train a token classifier model given a list of abstracts """
    raise NotImplementedError("Need to implement train()")
    
  def test(self, absList, modelfilename, entityTypes):
    """ Apply the token classifier to a given list of abstracts
        using the given model file.
        """
    raise NotImplementedError("Need to implement test()")
    
  def writeFeatureFile(self, absList, filename, entityTypes, tokenFilter, includeLabels):
    """ write features for each token to a file that can be read by 
        the classifier
        """
    raise NotImplementedError("Need to implement writeFeatureFile()")

  def entityTypesString(self, entityTypes):
    """ return string containing list of entity types """
    return '-'.join(entityTypes)
              
  def readLabelFile(self, labelFilename, entityTypes):
    """ read classifier output and return list of token labels.
        """
    raise NotImplementedError("Need to implement readLabelFile()")
        
  def returnsAlternateLabels(self):
    """ return True if classifier returns alternate labels for tokens """
    return self.topK > 1 
    

