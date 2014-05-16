#!/usr/bin/python
# Compute features for labeling noun phrases as group, outcome, other
# author: Rodney Summerscales

#import sys
#import Queue
import os
from basetokenclassifier import BaseTokenClassifier
from basetokenclassifier import TokenLabel


######################################################################
# Experimental mention finder
######################################################################

class MegamTokenClassifier(BaseTokenClassifier):
  """ Used for training/testing a classifier to label mention tokens 
      in a list of abstracts.
      """
  binaryThreshold = 0.5
      
  def __init__(self, binaryThreshold=0.5):
    """ Create a new mention finder to find a given list of mention types.
        entityTypes = list of mention types to find (e.g. group, outcome)
    """
    BaseTokenClassifier.__init__(self, 'megam')
    self.binaryThreshold = binaryThreshold
      
  def train(self, absList, modelFilename, entityTypes, tokenFilter=None):
    """ Train a mention finder model given a list of abstracts """

    featureFilename = 'features.'+self.entityTypesString(entityTypes)+'.train.txt'
            
    self.writeFeatureFile(absList, featureFilename, entityTypes, True, tokenFilter)

    if len(entityTypes) > 1:
      cType = 'multiclass'
    else:
      cType = 'binary'
    cmd = 'lib/megam/megam.opt -quiet  %s %s > %s' %(cType, featureFilename, modelFilename)
#    cmd = 'bin/megam.opt -quiet -tune binary ' + featureFilename + ' > ' \
#      + modelFilename
    print cmd  
    os.system(cmd)    


  def test(self, absList, modelFilename, labeledFilename, entityTypes, tokenFilter=None):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
    """  
    featureFilename = 'features.'+self.entityTypesString(entityTypes)+'.test.txt'

    self.writeFeatureFile(absList, featureFilename, entityTypes, True, tokenFilter)
    
    if len(entityTypes) > 1:
      cType = 'multiclass'
    else:
      cType = 'binary'
    cmd = 'lib/megam/megam.opt -quiet -predict %s %s %s > %s' %(modelFilename, cType, featureFilename, labeledFilename)
#    cmd = 'bin/megam.opt -quiet -predict ' + modelFilename + ' binary ' \
#       + featureFilename + ' > ' + labeledFilename 
    print cmd
    os.system(cmd)
          
  def readLabelFile(self, labelFilename, entityTypes):
    """ read a mallet label file and return the list of labels """
    labelLines = open(labelFilename, 'r').readlines()
    labelList = []
    
    if len(entityTypes) == 1:
      binaryClassification = True
    else:
      binaryClassification = False
      
    labelConversionList = ['other']
    for eType in entityTypes:
      labelConversionList.append(eType)
    
    for line in labelLines:
      parsedLine = line.strip().split()
      if len(parsedLine) > 0:
        mClass = int(parsedLine[0])
        prob = float(parsedLine[1])
        if binaryClassification:
          if prob < self.binaryThreshold:
            mClass = 0
          else:
            mClass = 1
        label = labelConversionList[mClass]   
        
        tLabel = TokenLabel(label)
        tLabel.prob = prob
        tLabel.sequenceProb = 1
        
        labelList.append([tLabel])
              
#        labelList.append(label) 
     
    return labelList
    
  def writeFeatureFile(self, absList, filename, entityTypes, includeLabels, tokenFilter=None):
    """ write features for each token to a file that can be read by 
        the Mallet simple tagger """
        
    labelConversionHash = {'other':'0'}
    i = 1
    for eType in entityTypes:
      labelConversionHash[eType] = str(i)
      i += 1
        
    featureFile = open(filename,'w')
    for abs in absList:
      s = 0
      for sentence in abs.sentences:
        for token in sentence.tokens:
          if tokenFilter == None or tokenFilter(token) == True: 
            # write the label for the token
            if includeLabels == True:
              # see if the token has one of the labels the finder will look for
              label='other'
              for mType in entityTypes:
                if token.hasAnnotation(mType):
                  label = mType
                  break
              featureFile.write(labelConversionHash[label]+' ')
            
            # write features for the token
            for featureSet in token.features.values():
              for feature in featureSet:
                try:
                  featureFile.write(feature+' ')
                except UnicodeEncodeError: 
                  print 'UnicodeEncodeError:',
                  print 'abs=',abs.id, 'sentence=', s, 'token=',token.index
                  print 'feature=', feature
                  featureFile.write(feature.encode('ascii', 'xmlcharrefreplace'))
            featureFile.write('\n')
#        featureFile.write('\n')
        s += 1
    featureFile.close()
           


