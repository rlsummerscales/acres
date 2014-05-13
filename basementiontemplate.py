#!/usr/bin/python
# author: Rodney Summerscales


import nltk
import numpy
import xmlutil
import sys
import math

from nltk.corpus import stopwords
from basetemplate import BaseTemplate

##############################################
# Base class definition for all MENTION templates
##############################################

class BaseMentionTemplate(BaseTemplate):
  """ Base class for all mention templates """
  name = ''    # name for the mention
  annotatedId = ''      # annotated id for the mention
  id = ''
  ignoreWords = set(['the','a','of', 'an', 'group', 'groups','arm', 'had'])
  mention = None  
  umlsCodes = None
  snomedCodes = None
  parent = None    # mention that this one has been merged into
  children = None  # list of mentions that have been merged with this one
  matched = False 
  exactMatch = False
  matchedTemplate = None 
  outcomeMeasurements = None
  
  def __init__(self, mention, mentionType, useAnnotations=False):
    """ initialize template given a mention """
    BaseTemplate.__init__(self, mentionType)
    self.mention = mention
    self.start = mention.start
    self.end = mention.end
    self.id = ''
    self.annotatedId = ''
    self.parent = None
    self.children = []
    self.matched = False
    self.exactMatch = False
    self.matchedTemplate = None
    self.outcomeMeasurements = []
    if self.mention.matchedMention != None or useAnnotations:
      if useAnnotations:
        annotatedMention = self.mention
      else:
        annotatedMention = self.mention.matchedMention

      # this mention has already been matched to an annotated mention
      # use the id from that mention
      for token in annotatedMention.tokens:
        # find first token with an id
        id = token.getAnnotationAttribute(self.type, 'id')
        if len(id) > 0:
          self.annotatedId = id
          break   
    self.name = self.mention.text.strip()
    self.umlsCodes = set([])
    self.snomedCodes = set([])
    for token in mention.tokens:
      for uc in token.umlsConcepts:
        self.umlsCodes.add(uc.id)
        if len(uc.snomed) > 0:
          self.snomedCodes.add(uc.snomed)
  
  def getAnnotatedId(self, checkEntireCluster=True):
    """ return the annotated ID for this mention or its cluster """
    if len(self.annotatedId) > 0:
      return self.annotatedId
    elif checkEntireCluster:
      if self.isRootMention():
        idList = {}
        for child in self.children:
          if len(child.annotatedId) > 0:
            if child.annotatedId not in idList:
              idList[child.annotatedId] = 0
            idList[child.annotatedId] += 1
        popID = ''
        for id in idList.keys():
          if len(popID) == 0 or idList[id] > idList[popID]:
            popID = id 
        return popID
      else:
        return self.rootMention().getAnnotatedId() 
    else:
      return ''
        
  def getCanonicalName(self):
    """ return the canonical name for the mention cluster """
    return self.name
    
  def umlsCodeString(self):
    """ return a string containing a comma separated list of UMLS codes
        for the mention. """
    return ','.join(self.umlsCodes)
    
  def snomedCodeString(self):
    """ return a string containing a comma separated list of SNOMED codes
        for the mention. """
    return ','.join(self.snomedCodes)

  def getSentence(self):
    """ return the sentence that contains this abstract """
    return self.mention.getSentence()

  def addOutcomeMeasurement(self, omTemplate):
    """ add an outcome measurement to list of outcome measurements for this mention """
    self.outcomeMeasurements.append(omTemplate)
    
  def getOutcomeMeasurements(self):
    """ return list of outcome measurements for this mention """
    rootMention = self.rootMention()
    omList = rootMention.outcomeMeasurements
    for child in rootMention.children:
      if len(child.outcomeMeasurements) > 0:
        omList += child.outcomeMeasurements
#    return list(set(omList))
    return omList

  def matchesTemplateExact(self, mTemplate):
    """ return True if the token sets from a given mention template match
        the token set from this templates. Do not ignore function words """
    if self == mTemplate:
      # easy case, they are the same object
      return True  
    else:
      return self.mention.exactMatch(mTemplate.mention)
  
  def exactSetMatch(self, mTemplate, ignoreSemanticTagList=[]):
    """ return True if the token sets from a given mention template match
        the token set from this templates. """
    if self == mTemplate:
      # easy case, they are the same object
      return True  
    else:
      return self.mention.exactSetMatch(mTemplate.mention, ignoreSemanticTagList)

  def inSameCluster(self, mTemplate):
    """ return True if the given mention template is in the same cluster as this one """
    return self.rootMention() == mTemplate.rootMention()

  def partialSetMatch(self, mTemplate, ignoreSemanticTagList=[]):
    """ return number of tokens matched if the root template in this cluster is a partial match 
        for the root template from another cluster. """
    nMatched = 0
    nUnmatched1 = 0
    nUnmatched2 = 0
    
    m1 = self.rootMention().mention
    m2 = mTemplate.rootMention().mention
    
    words1 = m1.importantWords(ignoreSemanticTagList)
    words2 = m2.importantWords(ignoreSemanticTagList)

#    words1 = m1.importantLemmas(ignoreSemanticTagList)
#    words2 = m2.importantLemmas(ignoreSemanticTagList)

    
    nMatched = len(words1.intersection(words2))
    nUnmatched1 = len(words1 - words2)
    nUnmatched2 = len(words2 - words1)

#    print 'Comparing: ', words1, words2
    return (nMatched, nUnmatched1, nUnmatched2)
        
    
  def matchAnnotated(self, annotatedTemplate, partialMatch=True):
    """ use the current scheme to determine if the mention for this template
        matches that of a given mention template."""
    # consider there to be a match if the root template for the detected
    # mention cluster matches one of the mentions in the annotated cluster
    
    (nMatched, nDetectedUnmatched, nAnnotatedUnmatched) = self.countOverlapWithAnnotated(annotatedTemplate)   
    
    # exact match
    if nMatched > 0 and nDetectedUnmatched == 0 and nAnnotatedUnmatched == 0:
      return True
    
    # partial match
    if partialMatch and nMatched > 0:
      return True
    else:
      return False

#     matched = False        
#     mention = self.rootMention().mention
#     annotatedTemplate = annotatedTemplate.rootMention()
#         
#     if mention.matchedMention == annotatedTemplate.mention \
#        or mention.exactSetMatch(annotatedTemplate.mention):
#       matched = True
#     else:
#       for child in annotatedTemplate.children:
#         if mention.matchedMention == child.mention \
#           or mention.exactSetMatch(child.mention):
#           matched = True
# 
#     return matched

  def countOverlapWithAnnotated(self, annotatedTemplate):
    """ find the mention in the given annotated template that matches the name of this
        template the best.
        Return the number of words matched, 
           the number of words in the name of this template that are unmatched,
           the number of words in the annotated template that are unmatched.
        In all cases, ignore stop words """
    
    nMatched = 0
    nDetectedUnmatched = 0
    nAnnotatedUnmatched = 0
    
    # consider there to be a match if the root template for the detected
    # mention cluster matches one of the mentions in the annotated cluster
#    mention = self.rootMention().mention
    mention = self.mention
    annotatedTemplate = annotatedTemplate.rootMention()
    
    # first check for exact matches    
    matchedMention = None        
    if mention.exactSetMatch(annotatedTemplate.mention):
      matchedMention = annotatedTemplate.mention
    else:
      for child in annotatedTemplate.children:
        if mention.exactSetMatch(child.mention):
          matchedMention = child.mention
          
    if matchedMention != None:
      # we had an exact match
      nMatched = len(mention.importantWords()) 
    else:
      # no match so far.
      # now check for matches where name mention physically overlaps an annotated mention
      # in a significant way.
      if mention.matchedMention == annotatedTemplate.mention:
        matchedMention = annotatedTemplate.mention
      else:
        for child in annotatedTemplate.children:
          if mention.matchedMention == child.mention:
            matchedMention = child.mention
      if matchedMention != None:
        # found a match, compute overlap
        dWords = mention.importantWords()
        aWords = matchedMention.importantWords()
        nMatched = len(dWords.intersection(aWords))
        nDetectedUnmatched = len(dWords - aWords)
        nAnnotatedUnmatched = len(aWords - dWords)
      else:
        # still no match found, try root mention if this isn't it
        if self.isRootMention() == False and self.rootMention() != None:
          # try to match using the root mention
          (nMatched, nDetectedUnmatched, nAnnotatedUnmatched) = self.rootMention().countOverlapWithAnnotated(annotatedTemplate)
        else:
          nDetectedUnmatched = len(mention.importantWords())
    
    return (nMatched, nDetectedUnmatched, nAnnotatedUnmatched)
  
  def setId(self, id):
    """ set the id for the mention cluster to a given string"""
    self.id = id
    for token in self.mention.tokens:
      token.setLabelAttribute(self.type, 'id', self.id)
    for child in self.children:
      child.id = self.id
  
  def merge(self, mTemplate):
    """ Merge new information from a given group template with this one.
        This operation leaves the given group template unchanged."""
    # merge the mention with the parent mention
    # all merges happen with the root mention
    # this is sort of a disjoint-set forest type of data structure
    if mTemplate.parent != None:
      mTemplate = mTemplate.rootMention()
      
    if self == mTemplate:
      return                 # nothing to merge
    elif self.parent != None:
      # need to use parent of this mention for merging
      self.parent.merge(mTemplate)
      self.umlsCodes = self.parent.umlsCodes
      self.snomedCodes = self.parent.snomedCodes
#      if len(self.id) == 0:
#        self.id = self.parent.id
      self.copyDataFromParent()
    else:
      # self is the parent mention, merge with this mention        
#      if len(self.id) == 0 and len(mTemplate.id) > 0:
#        self.id = mTemplate.id
      mTemplate.parent = self
      
      self.umlsCodes = self.umlsCodes.union(mTemplate.umlsCodes)
      self.snomedCodes = self.snomedCodes.union(mTemplate.snomedCodes)
      self.mergeMentionData(mTemplate)
      self.children.append(mTemplate)
      
      # merge any children of this mention template
      for child in mTemplate.children:
#        self.merge(child)
        self.children.append(child)
        child.parent = self
        
      mTemplate.children = []
      mTemplate.umlsCodes = self.umlsCodes
      mTemplate.snomedCodes = self.snomedCodes
#      if len(mTemplate.id) == 0:
#        mTemplate.id = self.id
      mTemplate.copyDataFromParent()

  def mergeMentionData(self, mTemplate):
    """ merge the mention specific data from a given mention with this
        mention.
        This mention (self) is the root mention. """
    raise NotImplementedError("Need to implement mergeMentionData()")

  def copyDataFromParent(self):
    """ copy the mention specific data from the parent mention """
    raise NotImplementedError("Need to implement copyDataFromParent()")

  def getMentionChain(self):
    """ return the list of mentions that supposedly refer to the same entity
       as this one. The list includes this mention."""
    if self.parent != None:
      return self.parent.getMentionChain()
    else:
      chain = [self] + self.children
      return chain
      
  def display(self):
    """ output the mention and its children for debugging purposes """
    self.write(sys.stdout)
    
  def write(self, out): 
    """ output contents of mention """
    if self.isRootMention() == False:
      self.parent.display()
    else:
      out.write('Root mention: %s %s\n'% (self.name, self.mention))
      for child in self.children:
        out.write('  --%s %s %s\n'% (child.name, child, child.mention))
        
  def rootMention(self):
    """ return the root mention for the entity that this mention refers to """
    if self.parent == None:
      return self
    else:
      return self.parent.rootMention()
  
  def isRootMention(self):
    """ return True if this mention is the root mention in the cluster """
    return self.rootMention() == self    

  def toString(self):
    """ return string describing this mention """
    return self.name
  
  def getClosestMention(self, targetTemplate, considerPreviousSentences=True):
    """ return the child mention that is the closest to a given entity. 
        Only consider sentence containing given entity and the preceeding sentences. 
        if two mentions are the same distance from target, give preference to the one that appears
        before the target.  """ 
    targetSentenceIdx = targetTemplate.getSentence().index
    
    closestMention = None
    closestSentenceIdx = -1
    shortestDistance = float('inf')

#    if self.type == 'group' and targetTemplate.type == 'eventrate':
#      print 'Finding closest mention to', targetTemplate.value
    
    for m in self.getMentionChain():
      mSentenceIdx = m.getSentence().index
      if mSentenceIdx < targetSentenceIdx:
        # in a previous sentence
        if considerPreviousSentences and (closestSentenceIdx < mSentenceIdx \
                                          or (mSentenceIdx == closestSentenceIdx and closestMention.end < m.start)):
          closestSentenceIdx = mSentenceIdx
          closestMention = m
      elif mSentenceIdx == targetSentenceIdx:
        # in same sentence as target, is it the closest in the sentence?
        dist = m.distanceToEntity(targetTemplate)
        if dist < shortestDistance \
           or (dist == shortestDistance and m.end < closestMention.start):  
          closestMention = m 
          closestSentenceIdx = mSentenceIdx
          shortestDistance = dist
#          if self.type == 'group' and targetTemplate.type == 'eventrate':
#            print targetTemplate.value, m.name, targetSentenceIdx, closestSentenceIdx, targetTemplate.end, m.start, dist, shortestDistance
          
#      sentenceDistance = targetSentence.index - m.getSentence().index
#      if 0 < sentenceDistance and sentenceDistance < shortestSentenceDistance:
#        # this mentions is in a sentence closer to the target
#        closestMention = m
#        shortestSentenceDistance = sentenceDistance
#      elif sentenceDistance == 0:
#        # in same sentence as target, is it the closest in the sentence?
#        dist = m.distanceToEntity(targetTemplate)
#        if dist < shortestDistance \
#           or (dist == shortestDistance and m.end < closestMention.start):  
#          closestMention = m 
#          shortestSentenceDistance = 0
#          shortestDistance = 0
#      elif sentenceDistance == shortestSentenceDistance:
#        # in same sentence as current closest mention. see if it is closer to end of sentence
#        if closestMention.end < m.start:
#          closestMention = m      
          
    return (closestMention, shortestDistance)
      
  def distanceToEntity(self, targetTemplate):
    """ if this mention is in the same sentence as a given entity, return the number of tokens between them.
        Otherwise, return infinity """
    distance = float('inf')
    if targetTemplate.getSentence() == self.getSentence() and self.getSentence() != None:
      if self.end < targetTemplate.start:
        # this mention appears BEFORE
        distance = targetTemplate.start - self.end - 1
      else:
        # this mention appears AFTER
        distance = self.start - targetTemplate.end - 1
        
    return distance      
      
      
      
            
  
  