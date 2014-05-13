#!/usr/bin/python
# author: Rodney Summerscales


import nltk
import numpy
import xmlutil
import sys
import math

from nltk.corpus import stopwords
from basementiontemplate import BaseMentionTemplate
from basetemplate import Evaluation


#############################################
# class definition for a group template
#############################################

class Group(BaseMentionTemplate):
  """ Manage information related to a group mention. """
  sizes = []    # list of group size templates
#  estimatedSize = None  # size estimated from another
  outcomeNumbers = [] # list of outcome number templates
  eventrates = [] 
  groupSizeEvaluation = None
  
  def __init__(self, mention, useAnnotations=False):
    """ initialize group template given a group mention """
    BaseMentionTemplate.__init__(self, mention, 'group', useAnnotations)
    self.sizes = []
    self.outcomeNumbers = []
    self.eventrates = []
    self.role = 'unknown'
    self.groupSizeEvaluation = Evaluation()
    if useAnnotations:
      for token in self.mention.tokens:
        groupRole = token.getAnnotationAttribute(self.type, 'role')
        if groupRole == 'control':
          self.role = groupRole
        elif groupRole == 'experiment':
          self.role = groupRole          
    else:  
      if self.isControl():
        self.role = 'control'
      if self.isExperiment():
        self.role = 'experiment'

  def hasSize(self, size):
    """ return true if this group has the given group size value """
    for gs in self.sizes:
      if gs.value == size:
        return True
    return False
    
  def exactSetMatch(self, mTemplate, ignoreSemanticTagList=['people']):
    """ return True if the token sets from a given mention template match
        the token set from this templates. """
    return BaseMentionTemplate.exactSetMatch(self, mTemplate, ignoreSemanticTagList)    

  def partialSetMatch(self, mTemplate, ignoreSemanticTagList=['people']):
    """ return number of tokens matched if the root template in this cluster is a partial match 
        for the root template from another cluster. """
    return BaseMentionTemplate.partialSetMatch(self, mTemplate, ignoreSemanticTagList)    
  
    
  def getSize(self, sentenceIndex=None, timeTemplate=None, maxSize=False):
    """ return size of group at a certain time specified by a time template.
        return 0 if no size specified at this follow-up time """
    if self.rootMention() != self:
      return self.rootMention().getSize(sentenceIndex, timeTemplate, maxSize)
    
    if len(self.sizes) == 0:
      return 0  # no group sizes found
      
    # only one size for this group, return it
#    if len(self.sizes) == 1:
#      return self.sizes[0].value
    
    # return largest size if asked for it
    if maxSize:
      largest = 0
      for gs in self.sizes:
        if gs.value > largest:
          largest = gs.value
      return largest
        
    # multiple group sizes and time specified
    # make sure gs was recorded at this time
    if timeTemplate != None:
      for gs in self.sizes:
        if gs.time != None and gs.time.id == timeTemplate.id:
          return gs.value
    if sentenceIndex != None:
      gs = self.getClosestGroupSize(sentenceIndex)
      if gs != None:
        return gs.value
      else:
        return 0
#    # return the most recent preceding group size relative to a give sentence index
#    if sentenceIndex != None:
#      mostRecentGS = None
#      minDist = 999
#      for gs in self.sizes:
#        dist = (sentenceIndex - gs.sentence.index)
#        if dist >= 0 and (sentenceIndex - gs.sentence.index) < minDist:
#           minDist = dist
#           mostRecentGS = gs
#      if mostRecentGS != None:
#        return mostRecentGS.value
#      else:   
#        return 0
    # if all else fails, just return the first one found
    return self.sizes[0].value
  
  def getClosestGroupSize(self, sentenceIndex):
    """ return the group size template that is closest to the sentence with the given sentence index """
    # return the most recent preceding group size relative to a give sentence index
    if self.rootMention() != self:
      return self.rootMention().getClosestGroupSize(sentenceIndex)
    
    mostRecentGS = None
    minDist = 999
    for gs in self.sizes:
      dist = (sentenceIndex - gs.sentence.index)
      if dist >= 0 and (sentenceIndex - gs.sentence.index) < minDist:
         minDist = dist
         mostRecentGS = gs
    if mostRecentGS != None:
      return mostRecentGS
    else:   
      return None
      
    
  
  def addSize(self, gsTemplate):
    """ add a new group size to this group """
#    print 'adding ', gsTemplate.value, 'to ', self.name, self.isRootMention()
    if self.isRootMention():
      self.sizes.append(gsTemplate)
    else:    
      rm = self.rootMention()
      rm.addSize(gsTemplate)
      self.sizes = rm.sizes
           
  def isControl(self):
    """ does the group name sound like the name of a control group? """
    tokens = self.mention.tokens.toLemmaSet()
    if 'control' in tokens or 'placebo' in tokens \
        or (('usual' in tokens or 'standard' in tokens) \
            and ('care' in tokens or 'treatment' in tokens)):
      return True
    else:
      for child in self.children:
        if child.isControl():
          return True
      return False

  def isExperiment(self):
    """ does the group name sound like the name of an experimental group? """
    tokens = self.mention.tokens.toLemmaSet()
    controlWords = set(['control', 'placebo', 'usual', 'standard'])
    if 'experiment' in tokens or 'experimental' in tokens \
        or (('treatment' in tokens or 'therapy' in tokens or \
          'intervention' in tokens) 
          and ('new' in tokens or len(tokens.intersection(controlWords))==0)): 
      return True
    else:
      for child in self.children:
        if child.isExperiment():
          return True

      return False

  def setId(self, id):
    """ set the ID for this group """
    id = 'g'+id
    BaseMentionTemplate.setId(self, id)

      
  def mergeMentionData(self, mTemplate):
    """ merge the mention specific data from a given mention with this
        mention """
    if self.parent != None:
      raise StandardError('mergeMentionData() called outside of merge()')
    
    # merge list of group sizes  
    if len(mTemplate.sizes) > 0:
      for gs in mTemplate.sizes:
        self.addSize(gs)
        gs.group = self
      mTemplate.sizes = self.sizes

#    print 'Merging:', self.name, self.sizes, mTemplate.sizes
          
    # add outcome number templates that are not already in this templates list
    for onTemplate in mTemplate.outcomeNumbers:
      if onTemplate not in self.outcomeNumbers:
        self.outcomeNumbers.append(onTemplate)
        onTemplate.group = self
        
  def copyDataFromParent(self):
    """ copy the mention specific data from the parent mention """
    if self.parent == None:
      return
    
    self.outcomeNumbers = self.parent.outcomeNumbers
    self.eventrates = self.parent.eventrates
    self.sizes = self.parent.sizes
     
  def write(self, out):
    """ write contents of template to output stream """
    BaseMentionTemplate.write(self,out)
    
        
       
  