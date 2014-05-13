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
from basequantitytemplate import BaseQuantityTemplate
from basementiontemplate import BaseMentionTemplate

#############################################
# Template for a population age value 
#############################################

class AgeValue(BaseQuantityTemplate):
  """ A mean, median, min, or max age value in an age phrase """
#  token = None
#  value = 0
#  type = None   # mean, median, min, max
  units = None  # days, weeks, years, months
  bounds = None  # value is +- some bounding value (stdev, variance, error)
  source = None
  matchesTrialRegistry = False
  
  def __init__(self, token=None, type=None, timeUnits=None, source='abstract'):
    """ create a new age value given a value token and a type """
    BaseQuantityTemplate.__init__(self, token, type)
#     self.token = token
#     if self.token != None:
#       self.value = token.getValue()
#     self.type = type
    self.units = timeUnits
    self.bounds = None
    self.source = source
    self.matchesTrialRegistry = False
  
  def toString(self):
    """ return string describing this age value """
    return self.type + ' = ' + str(self.value)

  def ageInHours(self):
    """ return the age value converted to hours. assume age in years if not specified """
    if self.units == None or self.units[0] == 'y':
      return self.value * 365 * 24
    elif self.units[0:2] == 'mo':
      return self.value * 30 * 24
    elif self.units[0] == 'w':
      return self.value * 7 * 24
    elif self.units[0] == 'd':
      return self.value * 24
    elif self.units[0] == 'h':
      return self.value
    elif self.units[0:2] == 'mi':
      return float(self.value) / 60
    elif self.units[0] == 's':
      return float(self.value) / 360 
    else: # unknown units
      print self.token.sentence.abstract.id, 
      print 'Warning: AGE value ',self.value,'has unknown units =', self.units
      return 0
    
  def getXML(self, doc):
    """ return xml node contain all information relevant to this age value"""
    node = xmlutil.createNodeWithTextChild(doc, 'AgeValue', str(self.value))
    if self.type != None:
      node.setAttribute('type',self.type)
    if self.units != None:
      node.setAttribute('units', self.units)
    if self.bounds != None:
      node.setAttribute('bounds', str(self.bounds))
    node.setAttribute('source', self.source)
    
    return node

#############################################
# Template for population age description
#############################################
    
    
class Age(BaseMentionTemplate):
  """ Contains information related to an age phrase that describes
      the age range of the trial participants. """

  values = None       # list of age values in this phrase
  trueValues = None   # list of true values in this phrase
  statisticTokenSet = set(['mean', 'median', 'med', 'avg', 'av', 'average'])
  nDiscardedValues = 0
  
  def __init__(self, mention, useAnnotations=False):
    """ initialize population template given an age mention
        if useAnnotation == True, then search the phrase for annotated
        age values and use those. Otherwise, use heuristics to identify 
        age values. """
    BaseMentionTemplate.__init__(self, mention, 'age')
    self.values = {}
    self.trueValues = {}
    self.nDiscardedValues = 0
    if useAnnotations:
      self.findAnnotatedValues(isGroundTruth=False)    
    else:
      self.findDetectedValues()
    self.findAnnotatedValues(isGroundTruth=True)
    
  def findAnnotatedValues(self, isGroundTruth):
    """ search the phrase for annotated age values and add those to list of 
        age values for the phrase """
    i = 0
    while i < len(self.mention.tokens):
      token = self.mention.tokens[i]
      if token.hasAnnotation('agevalue') and token.isNumber():
        type = token.getAnnotationAttribute('agevalue', 'type')
        units = token.getUnits()
        if type != None and len(type) > 0:
          av = AgeValue(token, type, units)
          if isGroundTruth:
            # for ground truth list, save every value
            if type not in self.trueValues:
              self.trueValues[type] = []
            self.trueValues[type].append(av)
          else:
            # for list of "detected values" only save one value for each type
            self.values[type] = av
          nextToken = token.nextToken()
          if nextToken != None and nextToken.text == 'plus_minus' and nextToken.nextToken().isNumber():
            i += 2
            token = self.mention.tokens[i]
            av.bounds = token.getValue() 
      i += 1
            
  def findDetectedValues(self):
    """ use heuristics to identify the values inside this mention """
    ageValues = []
    nextValType = None
    currentUnits = None
    for token in self.mention.tokens:
      text = token.text.lower()
      nextToken = token.nextToken()
      prevToken = token.previousToken()

      # pattern: MED/MEAN/AVG ... VAL
      if text in self.statisticTokenSet:
        if text[0:3] == 'med':
          nextValType = 'median'
        elif text == 'mean' or text[0:2] == 'av':
          nextValType = 'mean'
          
      # range pattern: BETWEEN ... VAL ... VAL
      if text == 'between':
        nextValType = 'min'
        
      # MIN/MAX patterns: GREATER/LESS THAN ... VAL        
      if text == 'than':
        if prevToken != None:
          if prevToken.text == 'greater':
            nextValType = 'min'
          elif prevToken.text == 'less':
            nextValType = 'max'
          
      if text == 'plus_minus':
        nextValType = 'bounds'
        
      # type of previous value is unknown. see if this token will help us
      # figure out what it should be.        

      # Range pattern: VAL ... TO ... VAL
      if len(ageValues) > 0 and text == 'to' \
        and (ageValues[-1].type == None or ageValues[-1].type == 'min'):
          nextValType = 'max'
          ageValues[-1].type = 'min'
 
      # MIN pattern: VAL ... OR/AND OLDER/MORE/GREATER/OVER
      # MAX pattern: VAL ... OR/AND YOUNGER/LESS/UNDER
      if len(ageValues) > 0 and ageValues[-1].type == None:
        if prevToken != None and (prevToken.text == 'or' or prevToken.text == 'and'):
          if text == 'older' or text == 'more' or text == 'greater' \
            or text == 'over':
            ageValues[-1].type = 'min'
          if text == 'younger' or text == 'less' or text == 'under':
            ageValues[-1].type = 'max'
             
      if token.isTimeUnitWord():
        currentUnits = token.text
        
      if token.isNumber():
        # check the next token to see if it provides the units
        if nextToken != None and nextToken.isTimeWord():
          timeUnits = nextToken.text
        else:
          timeUnits = currentUnits
        
        # MIN/MAX PATTERNS: OVER/UNDER VAL
        if nextValType == None:
          if prevToken != None: 
            if prevToken.text == 'under':
              nextValType = 'max'
            if prevToken.text == 'over':
              nextValType = 'min'       
          
        if nextValType == 'min':
          ageValues.append(AgeValue(token, nextValType, timeUnits))
          nextValType = 'max'
        elif nextValType == 'max' and len(ageValues) > 0 and \
           (token.getValue() < ageValues[-1].value \
             and ageValues[-1].units == timeUnits):
          # this is some other value, keep searching for MAX
          ageValues.append(AgeValue(token, None, timeUnits))
        elif nextValType == 'bounds':
          if len(ageValues) > 0:
            ageValues[-1].bounds = token.getValue()
            nextValType = None
        else:   
          # use whatever type we expected this one to be (MAX, MEAN, MEDIAN, None)     
          ageValues.append(AgeValue(token, nextValType, timeUnits))
          nextValType = None  

    # filter out values that cannot be age values.
    goodValues = []
    i = 0

    while i < len(ageValues):
      av = ageValues[i]
      if (av.token.specialValueType == None or av.token.specialValueType == 'time_value') \
         and av.value >= 0:
        # the value is probably a valid age value. it is not negative
        # and it has not been identified as another number
        goodValues.append(av)
      elif av.token.specialValueType == 'INTERVAL_BEGIN' and av.value >= 0 \
        and ((i-1) < 0 or (len(goodValues) > 0 and goodValues[-1] == ageValues[i-1]) \
                       or ((av.token.index - ageValues[i-1].token.index) > 2)) \
        and (i+1) < len(ageValues) \
        and ageValues[i+1].token.specialValueType == 'INTERVAL_END' \
        and ageValues[i+1].value >= 0:
        # this is the start of an interval. 
        # there is no previous value in sentence that has been discarded that
        # is near (within one token) of this value
        # the first and second values in the interval are non-negative
        goodValues.append(av)
        i += 1           
        goodValues.append(ageValues[i])
        
      i += 1
      
    self.nDiscardedValues = len(ageValues) - len(goodValues)
    ageValues = goodValues
      
    # If we have only one age value and we do not know what it is, 
    # assume it is the MEAN 
#    if len(ageValues) == 1 and ageValues[0].type == None:
#      ageValues[0].type = 'mean'
    
    # if we have just two unknown numbers and the first is less than the second,
    # assume that they are MIN and MAX
#     if len(ageValues) == 2 and ageValues[0].type == None \
#       and ageValues[1].type == None and ageValues[0].value < ageValues[1].value:
#       ageValues[0].type = 'min'
#       ageValues[1].type = 'max'
      
    for av in ageValues:
      if av.units == None and currentUnits != None:
        av.units = currentUnits
        
      if av.type != None:      
        if av.type in self.values:
          newValue = av.ageInHours()
          oldValue = self.values[av.type].ageInHours()
          if newValue != oldValue:
            # there are multiple different values of the same type
            # discard all values
            self.values = {}
            break
        else:
          # only value of this type so far
          self.values[av.type] = av
          
    # if there is a mean or median check to make sure that they are between the min and max
    checkVals = []
    if 'mean' in self.values:
      checkVals.append(self.values['mean'].ageInHours())
    if 'median' in self.values:
      checkVals.append(self.values['median'].ageInHours())
    
    if 'min' in self.values:
      minAge = self.values['min'].ageInHours()
    else:      
      minAge = -1

    if 'max' in self.values:
      maxAge = self.values['max'].ageInHours()
    else:      
      maxAge = 999999 

    for val in checkVals:
      if val < minAge or val > maxAge:
        # this value is beyond the bounds of the min/max age
        # discard all values
        self.values = {}
        break

#     valueLists = {'min':[], 'max':[], 'median':[], 'mean':[]}   
#     for av in ageValues:
#       if av.units == None and currentUnits != None:
#         av.units = currentUnits
#         
#       if av.type != None:      
#         valueLists[av.type].append([av.ageInHours(), av])
#         
# 
#     # find smallest min, largest max
#     if len(valueLists['min']) > 0:
#       valueLists['min'].sort()
#       minAge = valueLists['min'][0][0]
#     else:
#       minAge = -1       
# 
#     if len(valueLists['max']) > 0:
#       valueLists['max'].sort()
#       valueLists['max'].reverse()
#       maxAge = valueLists['max'][0][0]
#     else:
#       maxAge = 999999 
#       
#     if minAge < maxAge and len(valueLists['mean']) < 2 and len(valueLists['median']) < 2:
#       # the min is less than the max and there is only one mean/median value
#       if len(valueLists['mean']) == 1:
#         meanAge = valueLists['mean'][0][0]
#       else:
#         meanAge = (minAge+maxAge)/2  
# 
#       if len(valueLists['median']) == 1:
#         medianAge = valueLists['median'][0][0]
#       else:
#         medianAge = (minAge+maxAge)/2  
#       
#       if minAge < meanAge and meanAge < maxAge and minAge < medianAge and medianAge < maxAge:
#         # the median and mean (if they exist) are inside the min/max age values  
#         # keep all age values
#         for type in valueLists.keys():
#           if len(valueLists[type]) > 0:
#             self.values[type] = valueLists[type][0][1]
              
    
  def mergeMentionData(self, mTemplate):
    """ merge the mention specific data from a given mention with this
        mention """
    pass

  def copyDataFromParent(self):
    """ copy the mention specific data from the parent mention """
    pass

  def matchAnnotated(self, annotatedAgeMention):
    """ return true if this mention matches a given annotated mention.
        all of the values in the annotated mention must match values in 
        this mention for the two to be considered a match """
    if len(self.values) != len(annotatedAgeMention.values):
      return False
    for av in annotatedAgeMention.values.values():
      valueMatched = False
      for dAV in self.values.values():
        if av.type == dAV.type and av.value == dAV.value:
          valueMatched = True
          break
      if valueMatched == False:
        return False
    return True