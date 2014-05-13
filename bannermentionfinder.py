#!/usr/bin/python
# Use BANNER for mention finding
# author: Rodney Summerscales

import sys
import os.path
from basementionfinder import BaseMentionFinder

class BannerMentionFinder(BaseMentionFinder):
  """ A mention finder that uses the Biomed NER system BANNER 
      to identify mentions.
      """
  classpath = 'lib/banner/dragontool.jar:lib/banner/heptag.jar:' \
        +'lib/banner/mallet-deps.jar:lib/banner/mallet.jar:' \
        +'lib/banner/bc2.jar:lib/banner/banner.jar'
  propertyFilename = 'banner.properties'
  
  def __init__(self, entityTypes):
    """ Create a new mention finder to find a given list of mention types """
    BaseMentionFinder.__init__(self, entityTypes, None)
    self.finderType = 'banner'
   
  def computeFeatures(self, absList, mode='train'):
    """ compute classifier features for each token in each abstract in a
        given list of abstracts. """
    pass       # function does nothing. banner computes its own features

  def train(self, absList, modelFilename):
    """ Train a BANNER model given a list of abstracts
        (Ignores the model filename parameter.) """
    for mType in self.entityTypes:
      print mType
      # train phrase labeler
      banner = 'java -Xmx1000m -cp '+self.classpath+' bc2.TrainModel '
      sentenceFilename = mType+'.sentence.train.txt'
      mentionFilename = mType+'.mentions.train.txt'
      cmd = banner + ' ' + self.propertyFilename + ' ' + sentenceFilename + ' ' \
        + mentionFilename  + ' ' + mType 
  
      self.writeBannerFiles(absList, sentenceFilename, mentionFilename, mType)
      print cmd
      os.system(cmd)


    
  def test(self, absList, modelFilename, fold=None):
    """ Apply the mention finder to a given list of abstracts
        using the given model file.
        (Ignores the model filename parameter.)
        return mention finder statistics (MentionStats) object."""
    for mType in self.entityTypes:
      print mType
      banner = 'java -Xmx1000m -cp '+self.classpath+' bc2.TestModel ' 
      sentenceFilename = mType+'.sentence.test.txt'
      mentionFilename = mType+'.mentions.test.txt'
      resultFilename = mType+'/mention.txt'
      outputFilename = mType+'/output.txt'
      modelFilename = mType+'/model.bin'
      cmd = banner + ' ' + self.propertyFilename + ' ' + sentenceFilename + ' ' \
        + mentionFilename + ' '+ mentionFilename + ' ' \
        + modelFilename + ' ' + mType 
  
      self.writeBannerFiles(absList, sentenceFilename, mentionFilename, mType)
      print cmd
      os.system(cmd)
      
      self.assignLabels(outputFilename, absList, mType)
  
  def assignLabels(self, outputFilename, absList, mType):
      # store assigned labels in abstract list
      # read labeled phrase file
      lines = open(outputFilename, 'r').readlines()
      
      i = 0
      for abs in absList:
        for sentence in abs.sentences:
          line = lines[i].strip()
          labeledTokens = line.split()
          j = 0
          for token in sentence.tokens:
            # label is after '|'
            curLabeledToken = labeledTokens[j].split('|')
            label = curLabeledToken[-1]
            if token.text != curLabeledToken[0]:
              # banner split a token, try to merge it
              mergedTokens = curLabeledToken[0]
              while j < len(labeledTokens) \
                  and len(mergedTokens) < len(token.text):
                j = j + 1
                curLabeledToken = labeledTokens[j].split('|')
                mergedTokens = mergedTokens + curLabeledToken[0]
              if token.text != mergedTokens:
                # something is really wrong. token not just split
                print abs.id, '*** ERROR *** tokens do not match'
                print 'Original:', token.text, ', Labeled:', mergedTokens
                sys.exit()
            if label != 'O':
              token.addLabel(mType)
            j = j + 1
          i = i + 1


  def writeBannerFiles(self, absList, sentenceFilename, mentionFilename, mType):
    """ create files for finding mentions with BANNER """
    sFile = open(sentenceFilename, 'w')
    mFile = open(mentionFilename, 'w')
    specialTokens = set(['.', ')', ','])
    for abs in absList:
      for sentence in abs.sentences:
        sentenceId = '%s%d' % (abs.id, sentence.index)
        sFile.write(sentenceId)
        nChar = 0
        inMention = False
        curMention = []
        for token in sentence.tokens:
          if token.text not in specialTokens:
            sFile.write(' ')  # don't put space in front of certain tokens
          sFile.write(token.text)
          if token.hasAnnotation(mType):
            if inMention == False:
              # start new mention entry in mention file
              mFile.write(sentenceId+'|'+str(nChar)+' ')
              inMention = True
              curMention = [token.text]
            else:
              # continue current mention
              curMention.append(token.text)
          elif inMention == True:
            # end of mention. This token is not in current mention
            mFile.write(str(nChar-1)+'|'+' '.join(curMention)+'\n')
            curMention = []
            inMention = False
          nChar = nChar + len(token.text)
          if token == sentence.tokens[-1] and len(curMention) > 0:
            # last token in sentence, write it to file
            mFile.write(str(nChar-1)+'|'+' '.join(curMention)+'\n')
            curMention = []
            inMention = False
  
        sFile.write('\n') 
    sFile.close()
    mFile.close()
  

