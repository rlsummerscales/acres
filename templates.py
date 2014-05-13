#!/usr/bin/python
# author: Rodney Summerscales
# class definitions for group, outcome, outcome number 
# and summary statistic templates


import nltk
import numpy
import xmlutil
import sys
import math

from nltk.corpus import stopwords

from agetemplate import Age
from outcomemeasurementtemplates import OutcomeNumber, EventRate
from groupsizetemplate import GroupSize
from grouptemplate import Group
from outcometemplate import Outcome
from demographictemplates import Location, Population, Condition
from timetemplate import Time
from irstats import IRstats
from operator import itemgetter


def createMergedList(abstract, type):
  """ return a list of templates where similar templates of a given type
      have been merged. """
  list = []
  i = 0    
  for sentence in abstract.sentences:  
    if sentence.templates != None:  
      for sentenceTemplate in sentence.templates.getList(type): 
        foundMatch = False
        for abstractTemplate in list:
          if abstractTemplate.exactSetMatch(sentenceTemplate):
            foundMatch = True
            abstractTemplate.merge(sentenceTemplate)
            break
        if foundMatch == False:
          # template is unique so far, add it to the list
          list.append(sentenceTemplate)
          sentenceTemplate.id = str(i)
          i += 1
  return list
  
def createAnnotatedMergedList(abstract, type):
  """ return a list of templates where annotated templates of a given type
      have been merged based on their annotated id. """
  list = []
  i = 0 

  for sentence in abstract.sentences:    
    for sentenceTemplate in sentence.annotatedTemplates.getList(type): 
      foundMatch = False
      for abstractTemplate in list:
        if (abstractTemplate.getAnnotatedId() == sentenceTemplate.getAnnotatedId() \
            and len(abstractTemplate.getAnnotatedId()) > 0) \
          or abstractTemplate.exactSetMatch(sentenceTemplate):
          foundMatch = True
          abstractTemplate.merge(sentenceTemplate)
          break
      if foundMatch == False:
        # template is unique so far, add it to the list
        list.append(sentenceTemplate)
        i += 1
  return list


def countMatches(annotatedTemplates, detectedTemplates, errorOut):
  """ return RPF statistics given list of annotated and detected entities """
  stats = IRstats()
  # first find set of matching templates for each detected and annotated template
  potentialMatches = {}
  for aTemplate in annotatedTemplates:
    potentialMatches[aTemplate] = []
  for dTemplate in detectedTemplates:
    potentialMatches[dTemplate] = []
    for aTemplate in annotatedTemplates:
      if dTemplate.matchAnnotated(aTemplate):
        potentialMatches[dTemplate].append(aTemplate)
        potentialMatches[aTemplate].append(dTemplate)
      
  
  # check matches for each detected template
  for dTemplate in detectedTemplates:
    matchingAnnotatedTemplates = potentialMatches[dTemplate]
    if len(matchingAnnotatedTemplates) == 1:
      # there is only one annotated template that matches this detected one
      # this is either a TP or a DUPLICATE
      aTemplate = matchingAnnotatedTemplates[0]
      if len(potentialMatches[aTemplate]) == 1:
        # this detected template matches only ONE annotated one, count as TP
        stats.incTP()
        errorOut.write('  +TP: '+dTemplate.name + ' == ')
        errorOut.write(aTemplate.name+'\n')    
        aTemplate.matched = True
        dTemplate.matched = True
        if dTemplate.exactSetMatch(aTemplate):
          dTemplate.exactMatch = True
          aTemplate.exactMatch = True
        dTemplate.evaluation.markCorrect()
        dTemplate.matchedTemplate = aTemplate
        aTemplate.matchedTemplate = dTemplate
    else:
      # prune away all detected templates that match multiple annotated templates
#       if dTemplate.type == 'outcome':
#         print dTemplate.name, 'has multiple matches'
      if len(matchingAnnotatedTemplates) > 0:
        multipleMatches = True
      else:
        multipleMatches = False
        
      for aTemplate in matchingAnnotatedTemplates:
        potentialMatches[aTemplate].remove(dTemplate)
#         if dTemplate.type == 'outcome':
#           print 'Discarding from:', aTemplate.name
#           aTemplate.write(sys.stdout)
#           print dTemplate.mention.exactSetMatch(aTemplate.mention),
#           print dTemplate.mention.matchedMention == aTemplate.mention
#           for child in aTemplate.children:
#             print 'child:', child.name,
#             print dTemplate.mention.exactSetMatch(child.mention),
#             print dTemplate.mention.matchedMention == child.mention,
#             print dTemplate.mention.importantWords()
#             print child.mention.importantWords()
#           print
          
      potentialMatches[dTemplate] = []
      stats.incFP()
      errorOut.write('  -FP: %s, (MultipleMatches=%s)\n'%(dTemplate.name, multipleMatches))
      dTemplate.evaluation.markIncorrect()
      
  # check matches for each annotated template    
  for aTemplate in annotatedTemplates:
    dMatchList = potentialMatches[aTemplate]
    if len(dMatchList) == 0:
      # annotated template was unmatched, count as FN
      stats.incFN()
      errorOut.write('  -FN: '+aTemplate.name + '\n')      
    elif len(dMatchList) > 1:
      # annotated template matched multiple detected ones
      # find best match and count that one as a TP, the rest as duplicates
      # Best match is:
      #  1. Detected template name is an exact match for mention in true template
      #      -- for ties, go with first detected template with most matching non-stop words
      #  2. Partial match with most non-stop words matching true mention
      #      -- for ties, choose detected mention with fewest extra words not in true mention
      #             then the one with fewest unmatched words in true mention
      #             finally, if needed, choose first detected match
      
      exactMatches = []
      partialMatches = []
      for dTemplate in dMatchList:
        (nMatched, nDetectedUnmatched, nAnnotatedUnmatched) = dTemplate.countOverlapWithAnnotated(aTemplate)
        if nDetectedUnmatched == 0 and nAnnotatedUnmatched == 0:
          # exact match
          exactMatches.append((nMatched, dTemplate))
        else:
          partialMatches.append((nMatched, nDetectedUnmatched, nAnnotatedUnmatched, dTemplate))
      
      duplicates = []
      if len(exactMatches) > 0:
        # count best match
        exactMatches = sorted(exactMatches, reverse=True)
        dTemplate = exactMatches[0][1]
        aTemplate.matched = True
        dTemplate.matched = True
        dTemplate.exactMatch = True
        aTemplate.exactMatch = True
        dTemplate.matchedTemplate = aTemplate
        aTemplate.matchedTemplate = dTemplate
        dTemplate.evaluation.markCorrect()
        stats.incTP()
        errorOut.write('  +TP: '+dTemplate.name + ' == ')
        errorOut.write(aTemplate.name+'\n')    
        for (nMatched, dTemplate) in exactMatches[1:]:
          duplicates.append(dTemplate)
          dTemplate.exactMatch = True
          
      if len(partialMatches) > 0:
        if aTemplate.matched == False:
          partialMatches = sorted(partialMatches, key=itemgetter(1,2))
          partialMatches = sorted(partialMatches, key=itemgetter(0), reverse=True)
          dTemplate = partialMatches[0][3]
          aTemplate.matched = True
          dTemplate.matched = True
          dTemplate.matchedTemplate = aTemplate
          aTemplate.matchedTemplate = dTemplate
          dTemplate.evaluation.markCorrect()
          stats.incTP()
          errorOut.write('  +TP: '+dTemplate.name + ' == ')
          errorOut.write(aTemplate.name+'\n')    
          duplicatesStartIdx = 1
        else:
          # partial matches are all duplicates
          duplicatesStartIdx = 0
        
        for i in range(duplicatesStartIdx, len(partialMatches)):
          duplicates.append(partialMatches[i][3])
          
      for dTemplate in duplicates:
        dTemplate.matchedTemplate = aTemplate
        dTemplate.evaluation.markDuplicate()
        stats.incDuplicates() 
        errorOut.write('  =DUP: '+dTemplate.name + ' == ')
        errorOut.write(aTemplate.name+'\n')    

  return stats

      
########################################################
# class definition for all the templates in a sentence
########################################################

class Templates:
  lists = {}           # hash of template lists
  summaryStats = []
  sentence = None     # sentence object from which templates are filled
  featureVectors = [] # feature vectors for associating templates
  useLabels = True
  mentionTypes = ['population', 'condition', 'age', 'group', 'outcome', 'time',\
                    'location']
  quantityTypes = ['gs', 'on', 'eventrate']
  
  def __init__(self, sentence=None, useLabels=True):
    self.clear()
    if sentence != None:
      self.createTemplates(sentence, useLabels)

  def clear(self):
    self.lists = {}
    for type in self.mentionTypes:
      self.lists[type] = []
    for type in self.quantityTypes:
      self.lists[type] = []

    self.summaryStats = []
    self.featureVectors = []
    self.sentence = None
    self.useLabels = True

  def noTemplates(self):
    for list in self.lists.values():
      if len(list) > 0:
        return False
    return True

  def parse(self, node, sentence):
    self.clear()

  # fill templates for a given sentence object
  def createTemplates(self, sentence, useLabels, displayDebug = False):
    self.clear()
    self.sentence = sentence
    self.useLabels = useLabels

    mLists = {}
    if useLabels == True:
      for type in self.mentionTypes:
        mLists[type] = sentence.getDetectedMentions(type)
    else:
      for type in self.mentionTypes:
        mLists[type] = sentence.getAnnotatedMentions(type)

    useAnnotations = not useLabels
       
    for type in self.mentionTypes:    
      for mention in mLists[type]:
        if type == 'population':
          template = Population(mention)
        elif type == 'age':
          template = Age(mention, useAnnotations)
        elif type == 'time':
          template = Time(mention)
        elif type == 'location':
          template = Location(mention)
        elif type == 'condition':
          template = Condition(mention, useAnnotations)
        elif type == 'group':
          template = Group(mention, useAnnotations)
        elif type == 'outcome':
          template = Outcome(mention, useAnnotations)
        self.lists[type].append(template)
          
    i = 0
    while i < len(sentence):
      token = sentence[i]
      # create group size/outcome number templates as needed
      if token.isNumber():
        label = ''
        if useLabels == True:
          if token.hasLabel('gs'):
            label = 'gs'
          elif token.hasLabel('on'):
            label = 'on'
          elif token.hasLabel('eventrate'):
            label = 'eventrate'  
        else:
          if token.hasAnnotation('gs'):
            label = 'gs'
          elif token.hasAnnotation('on'):
            label = 'on'
          elif token.hasAnnotation('eventrate'):
            label = 'eventrate'  

        if label == 'gs':
          gs = GroupSize(token)
          self.lists[label].append(gs)
        elif label == 'eventrate':
          er = EventRate(token)
          self.lists[label].append(er)
        elif label == 'on':
          on = OutcomeNumber(token)
          self.lists[label].append(on)
          if i+2 < len(sentence.tokens):
            t2 = sentence[i+1]
            t3 = sentence[i+2]
            if (t2.text == 'of' or t2.text == '/') and t3.hasLabel('gs'):
              # next number is group size, associate it with this outcome number
              i = i + 2   # already processed the next two tokens
              gs = GroupSize(t3)
#              self.lists['gs'].append(gs)
              on.groupSize = gs
              gs.outcomeNumber = on
              
      i = i + 1  
      
#    for (key, value) in self.lists.items():
#      print key, len(value)

  def getList(self, type):
    """ return list of templates of a given template type """
    return self.lists.get(type, [])

  def addOutcomeMeasurementList(self, omList):
    """ add list of outcome measurement templates """
    self.lists['outcomemeasurement'] = omList
    
  def getOutcomeMeasurementList(self):
    """ return list of outcome measurement templates for sentence """
    return self.getList('outcomemeasurement')

  def closestMention(self, qTemplate, mType):
    """ find the mention that is closest to a given value
        return template of closest mention of correct type or None if none found
        If two mentions are at the same distance, it returns the mention that appears before the value in the sentence.
        
        qTemplate is a template for the quantity in question
        mType is the type of mention that we want to find
        """
    closest = None
    minDist = len(self.sentence)
    mTemplateList = self.getList(mType)
    for mTemplate in mTemplateList:
      d = qTemplate.token.index - mTemplate.mention.start
      if d < 0:
        d = -d
      if d < minDist:
        minDist = d
        closest = mTemplate
    return (closest, minDist)

  def templateBetween(self, type, start, end):
    """ return True if there is a template between two token indices in the 
        sentence (inclusive) """
    for template in self.getList(type):
      if template.start >= start and template.start <= end:
        return True
    return False


  def writeAssociations(self, out):
    """ output mention quantity associations to given output stream """ 

    for er in self.getList('eventrate'):
      out.write('Event rate: '+ str(er.value)+', outcome: ')
      if er.outcome != None:
        out.write(er.outcome.name)
        if er.shouldBeAssociated(er.outcome) == False:
          out.write('***')
      else:
        out.write('NONE ***')
      out.write(', group: ')
      if er.group != None:
        out.write(er.group.name)
        if er.shouldBeAssociated(er.group) == False:
          out.write('***')
      else:
        out.write('NONE ***')
      out.write('\n')

    for on in self.getList('on'):
      out.write('Outcome number: '+ str(on.value)+', outcome: ')
      if on.outcome != None:
        out.write(on.outcome.name)
        if on.shouldBeAssociated(on.outcome) == False:
          out.write('***')
      else:
        out.write('NONE ***')
      out.write(', group: ')
      if on.group != None:
        out.write(on.group.name)
        if on.shouldBeAssociated(on.group) == False:
          out.write('***')
      else:
        out.write('NONE ***')
      out.write('\n')
    for gs in self.getList('groupsize'):
      out.write('Group size: '+ str(gs.value) + ', group: ')
      if gs.group != None:
        out.write(gs.group.name)
        if gs.shouldBeAssociated(gs.group) == False:
          out.write('***')
      else:
        out.write('NONE ***')
      out.write('\n')
 
    

      


