#!/usr/bin/python
# author: Rodney Summerscales
# class definitions for group, outcome, outcome number 
# and summary statistic templates


import sys
import math
import baseoutcomevaluetemplate

#############################################
# class definition for an outcome number template
#############################################

class OutcomeNumber(baseoutcomevaluetemplate.BaseOutcomeValueTemplate):
  """ manage the information relevant to an Outcome number template """
  textEventrate = None
  outcomeMeasurement = None  # link to outcome measurement template

  def __init__(self, token):
    """ Initialize an outcome number template given an integer token object """
    baseoutcomevaluetemplate.BaseOutcomeValueTemplate.__init__(self, token, 'on')
    self.textEventrate = None
    self.outcomeMeasurement = None

  def groupSizeIsCorrect(self):
    """ return True if the outcome number has an associated group size and it is correct """
    if self.groupSize == None:
      return False
    else:
      return self.shouldBelongToSameOutcomeMeasurement(self.groupSize)

  
  def addTextEventrate(self, erTemplate):
    """ associate this number with given event rate """
    if self.textEventrate != None:
      # this outcome number is associated with another event rate
      # delete the association
      self.textEventrate.outcomeNumber = None
    
    self.textEventrate = erTemplate
    self.textEventrate.outcomeNumber = self

  def getGroupSize(self):
    """ return the group size value for this template """
    if self.groupSize != None:
      return self.groupSize.value
    elif self.group != None:
      size = self.group.getSize(sentenceIndex=self.token.sentence.index, \
                                timeTemplate=self.time)
      return size
    else:
      return 0

  def isComplete(self):
    """ return true if this template has all of the info it needs to be used """
    if (self.outcome != None and self.group != None \
        and self.getGroupSize() > 0):
      return True
    else:
      return False

  def getBadOutcomes(self):
    """ return the number of bad outcomes """
    if self.outcome != None and self.outcome.outcomeIsBad() == False \
      and self.getGroupSize() > 0:
#    if self.outcomeIsBad == False:
      # need to convert number of good outcomes to number of bad outcomes
      return (self.getGroupSize() - self.value)
    else:
      return self.value

  def hasAssociatedGroupSize(self):
    """ return True if this value is associated with a group size, e.g. 35 of 100 people had X """
    return self.groupSize != None
  
  def getOutcomes(self):
    """ return the number of outcomes """
    return self.value
          
  def eventRate(self, groupSize=0):
    """ compute the event rate """
    if groupSize <= 0:
      groupSize = self.getGroupSize()
    if groupSize == 0:
      print 'Error: Cannot determine event rate for outcome number. Group size unknown.'
      sys.exit(1)
      return 0.0
    er = float(self.value)/groupSize
    return er

  def hasEventRate(self):
    """ return True if can compute event rate """
    return self.getGroupSize() > 0
  
  def equivalentEventRates(self, eventrate):
    """ return True if the event rate for this template is equivalent to a given
        event rate. Compares rounded percentages. 
        maxDifference is """
#    if on.isComplete() == False or self.isComplete() == False:
#      return False
    
    if self.hasEventRate() == False:
      return False
    
    er1 = 100*self.eventRate()
    er2 = 100*eventrate
    
    if er1 > er2:
      largerER = er1
      smallerER = er2
    else:
      largerER = er2
      smallerER = er1
      
    return int(round(smallerER)) == int(round(largerER)) or int(math.floor(smallerER)) == int(math.floor(largerER)) \
      or  int(math.ceil(smallerER)) == int(math.floor(largerER))

     
  def eventRateString(self):
    """ return a formatted string containing the event rate """
    if self.isComplete():
      return '%.2f%%' % (100*self.eventRate())
    else:
      return ''

  def display(self):
    self.write(sys.stdout) 

  def write(self, out):
    """ write template info to file """
    out.write('Outcome: ')
    if self.outcome != None:
      out.write(self.outcome.name)
    else:
      out.write('---')

    out.write(', Group: ')
    if self.group != None:
      out.write(self.group.name)
    out.write(', '+str(self.getOutcomes())+'/')
    size = self.getGroupSize()
    if size > 0:
      out.write(str(size))
    else:
      out.write('---')
    out.write('\n')


#############################################
# class definition for an outcome number template
#############################################

class EventRate(OutcomeNumber):
  """ manage the information relevant to an event rate number """
  outcomeNumber = None
  
  def __init__(self, token=None):
    """ create a new template for a token containing an event rate """
    OutcomeNumber.__init__(self, token)
    self.outcomeNumber = None
    self.type = 'eventrate'
    if self.token.isPercentage() or self.value > 1:
      # normalize to range [0, 1]
      self.value = float(self.value)/100
     
  def eventRate(self):
    """ return the event rate """
    return self.value

  def hasEventRate(self):
    return True
  
  def addOutcomeNumber(self, onTemplate):
    """ associate this event rate with given outcome number """
    if self.outcomeNumber != None:
      # this event rate is associated with another outcome number
      # delete the association
      self.outcomeNumber.textEventrate = None
    
    self.outcomeNumber = onTemplate
    self.outcomeNumber.textEventrate = self
  
  def addTextEventrate(self, erTemplate):
    pass
  
  def badEventRate(self):
    """ return the bad event rate """
    if self.outcome != None and self.outcome.outcomeIsBad() == False:
      return 1-self.value
    else:
      return self.value

  def isComplete(self):
    """ return true if this template has all of the info it needs to be used """
    return self.outcome != None and self.group != None
 
  def getBadOutcomes(self):
    """ return the number of bad outcomes """
    return ''

  def getOutcomes(self):
    """ return the number of bad outcomes """
    return ''
        
  def toString(self):
    """ return a string containing all relevant info for this value """
    s = str(self.value) 
    if self.group != None:
      s += ', GROUP = '+self.group.name + ', prob = ' + str(self.groupProb)
    if self.outcome != None:
      s += ', OUTCOME = '+self.outcome.name + ', prob = ' + str(self.outcomeProb)
    return s 
      
  def write(self, out):
    """ write template info to file """
    out.write('Outcome: ')
    if self.outcome != None:
      out.write(self.outcome.name)
    else:
      out.write('---')

    out.write(', Group: ')
    if self.group != None:
      out.write(self.group.name)
    out.write(', '+self.eventRateString())      
    out.write('\n')

########################################################
# Template for outcome results for one treatment group
########################################################
  
class OutcomeMeasurement:
  """ All values relevant to an outcome measurement 
      (event rate, number of good/bad outcomes, size of group at the time)
  """
  __outcome = None
  __group = None
  __time = None
  __eventRate = None
  __outcomeNumber = None
  used = False        # has this measurement been used in a summary stat
  correctlyMatched = False     # has this been matched to an annotated outcome measurement
                      # (this is only used for OMs not part of an ARR calculation
  matchingOM = None
  
  def __init__(self, template=None):
    self.__outcome = None
    self.__group = None
    self.__time = None
    self.__eventRate = None
    self.__outcomeNumber = None
    self.used = False
    self.correctlyMatched = False
    self.matchingOM = None
    if template != None:
      if template.type == 'on':
        self.addOutcomeNumber(template)
      elif template.type == 'eventrate':
        self.addEventRate(template)
  
  def addGroup(self, gTemplate):
    """ add description of group """
    if gTemplate != None:
      self.__group = gTemplate
      self.__group.addOutcomeMeasurement(self)
    
      if self.__eventRate != None:
        self.__eventRate.group = self.__group
      if self.__outcomeNumber != None:
        self.__outcomeNumber.group = self.__group

  def addTime(self, tTemplate):
    """ add time when outcome was measured """
    if tTemplate != None:
      self.__time = tTemplate
      self.__time.addOutcomeMeasurement(self)

      if self.__eventRate != None:
        self.__eventRate.time = self.__time
      if self.__outcomeNumber != None:
        self.__outcomeNumber.time = self.__time

    
  def addOutcome(self, oTemplate):
    """ add template for outcome measured to outcome measurement """
    if oTemplate != None:
#      self.__outcome = oTemplate.rootMention()
      self.__outcome = oTemplate
      self.__outcome.addOutcomeMeasurement(self)

      if self.__eventRate != None:
        self.__eventRate.outcome = self.__outcome
      if self.__outcomeNumber != None:
        self.__outcomeNumber.outcome = self.__outcome
  
  def addEventRate(self, erTemplate):
    """ add template for outcome event rate """
    if self.__eventRate != None:
      # replacing existing event rate
      # previous event rate should no longer point to this template
      self.__eventRate.outcomeMeasurement = None
      
    self.__eventRate = erTemplate
    erTemplate.outcomeMeasurement = self
    
    if self.__outcomeNumber != None:
      self.__outcomeNumber.addTextEventrate(erTemplate)
    
    if self.__outcome != None:
      # event rate's outcome unknown (may happen with annotated)
      self.__eventRate.outcome = self.__outcome
    elif erTemplate.outcome != None:
      # this templates outcome unknown (may happen with detected)
      self.addOutcome(erTemplate.outcome)
      
    if self.__group == None:
      self.__group = erTemplate.group     
  
  def addOutcomeNumber(self, onTemplate):
    """ add template for number of good/bad outcomes """
    if self.__outcomeNumber != None:
      # replacing existing outcome number
      # previous outcome number should no longer point to this template
      self.__outcomeNumber.outcomeMeasurement = None

    self.__outcomeNumber = onTemplate
    onTemplate.outcomeMeasurement = self
    
    if self.__eventRate != None:
      self.__eventRate.addOutcomeNumber(onTemplate)
    
    if self.__outcome != None:
      self.__outcomeNumber.outcome = self.__outcome
    elif onTemplate.outcome != None:
      # this templates outcome unknown (may happen with detected)
      self.addOutcome(onTemplate.outcome)
      
    if self.__group == None:
      self.__group = onTemplate.group     
  
  def replaceWithEventRate(self, erTemplate):
    """ delete the outcome number information and replace it with information from 
       the given event rate """
    self.__outcomeNumber = None
    self.addEventRate(erTemplate)
  
  def getSentence(self):
    """ return the sentence containing the outcome measurement """
    if self.__eventRate != None:
      return self.__eventRate.getSentence()
    elif self.__outcomeNumber != None:
      return self.__outcomeNumber.getSentence()
  
  def getAbstract(self):
    """ return the abstract containing this outcome measurement """
    return self.getSentence().abstract
          
  def getOutcome(self):
    """ return template for outcome measured """
    return self.__outcome
    
  def getGroup(self):
    """ return template for group for which outcome was measured """
    return self.__group
    
  def getTime(self):
    """ return template for time when outcome was measured """
    return self.__time
  
  def getCompareSetID(self):
    """ return the annotated compareSet id value for the values in this outcome measurement
        or None if none given """
    csIDer = None
    csIDon = None
    if self.__eventRate != None:
      csIDer = self.__eventRate.token.getAnnotationAttribute('eventrate', 'compareSet')    
    if self.__outcomeNumber != None:
      csIDon = self.__outcomeNumber.token.getAnnotationAttribute('on', 'compareSet')    
    if csIDer != csIDon and self.__eventRate != None and self.__outcomeNumber != None:
      absID = self.__eventRate.token.sentence.abstract.id
      sID = self.__eventRate.token.sentence.index
      print '%s(%d): Error - Event rate (%f) and outcome number (%d) have different compareSet values.'\
               %(absId, sID, self.__eventRate.value, self.__outcomeNumber.value)
      sys.exit()
    elif csIDer != None and len(csIDer) > 0:
      return csIDer
    elif csIDon != None and len(csIDon) > 0:
      return csIDon
    
    return ''

  def getOutcomeNumber(self):
    """ return the number of outcomes (if specified) """
    return self.__outcomeNumber
  
  def getTextEventRate(self):
    """ return the event rate given in the original text (if specified) """
    return self.__eventRate
  
  def matchAnnotatedMentions(self, annotatedOM):
    """ return True if the mentions in this template match those in the given annotated
        outcome measurement template """
#     print self.getGroup().matchAnnotated(annotatedOM.getGroup())
#     print self.getOutcome().matchAnnotated(annotatedOM.getOutcome())
# 
#     print self.getGroup().name, self.getGroup().rootMention().mention.matchedMention
#     print annotatedOM.getGroup().name
#     print self.getOutcome().name, self.getOutcome().rootMention().mention.matchedMention
#     print annotatedOM.getOutcome().name
#     annotatedOM.getGroup().rootMention().display()
#     annotatedOM.getOutcome().rootMention().display()

    if self.getGroup() == None or annotatedOM.getGroup() == None \
      or self.getGroup().matchAnnotated(annotatedOM.getGroup()) == False:
      return False
    if self.getOutcome() == None or annotatedOM.getOutcome() == None \
      or self.getOutcome().matchAnnotated(annotatedOM.getOutcome()) == False:
      return False
#     if (self.getTime() == None and annotatedOM.getTime() != None) \
#        or (self.getTime() != None \
#             and self.getTime().matchAnnotated(annotatedOM.getTime()) == False):
#       return False
      
    return True
     
  def hasEventRateValue(self):
    """ return True if the outcome has an event rate value extracted from the text """
    return self.__eventRate != None
    
  def hasCalculatedEventRate(self):
    """ return True if the outcome has enough info to calculate the event rate """
    return self.__outcomeNumber != None and self.getGroupSize() > 0
       
  def eventrateValueOnly(self):
    """ Return true if the measurement only has an event rate value, 
        and cannot calculate an event rate. """
    return self.__eventRate != None and self.__outcomeNumber == None
  
  def calculatedEventRateOnly(self):
    """ return true if the event rate is calculated from outcome number,
        and there is no event rate number. """
    return self.__eventRate == None and self.eventRate() > -1
           
  def outcomeNumberConfidence(self):
    """ return the confidence score [0, 1] for the outcome number """
    if self.__outcomeNumber != None:
      return self.__outcomeNumber.confidence()
    else:
      return 0  # no outcome number  

  def eventRateConfidence(self):
    """ return the confidence score [0, 1] for the event rate """
    if self.__eventRate != None:
      return self.__eventRate.confidence()
    else:
      return 0  # no event rate
 
  def getConfidence(self):
    """ return confidence score for this template (i.e. how confident we are
      in the accuracy of the event rate and correctness of association) """
    if self.__eventRate == None and self.__outcomeNumber == None:
      return 0  
    
    if self.__outcomeNumber != None:
      onConfidence = self.outcomeNumberConfidence()
    else:
      onConfidence = 1.0
    
    if self.__eventRate != None:
      erConfidence = self.eventRateConfidence()
    else:
      erConfidence = 1.0
    
    return onConfidence * erConfidence

            
  def eventRate(self, useTextFirst=False, nEventRateDigits=3):
    """ return the bad event rate 
        if there is a group size reported with an outcome number, 
          use calculated event rate
        else, if there is a group size found earlier in paper,
          use calculated event rate
        else, if there is an event rate specified, use that
        else, return None (cannot calculate event rate)
        
        if useTextFirst == True, then use the event rate given in the text. If none is given
           in the text, then compute the event rate from outcome number and group size
    """
    if useTextFirst and self.__eventRate != None:
      return self.__eventRate.eventRate()
    
    eventrate = None
    if self.outcomeNumberHasGroupSize():
      on = self.getOutcomes()
      gs = self.__outcomeNumber.groupSize.value
      eventrate = float(on)/gs         
    elif self.__outcomeNumber != None and self.__group != None:
      on = self.getOutcomes()
      if on == 0:
        eventrate = 0.0
      else:  
        onToken = self.__outcomeNumber.token    
        gs = self.__group.getSize(sentenceIndex=onToken.sentence.index, \
                                   timeTemplate=self.__time)
#        gs = self.getGroupSize()
        if gs > 0: # and abs(float(on)/gs) <= 1:
          eventrate = float(on)/gs   
      
    if eventrate < 0 and self.__eventRate != None:
      eventrate = self.__eventRate.eventRate()
      
    if eventrate != None: 
      multiplier = math.pow(10, nEventRateDigits)      
      return round(eventrate*multiplier)/multiplier
    else:
      return None

  def outcomeNumberHasGroupSize(self):
    """ return true if a group size was given with the outcome number """
    return self.__outcomeNumber != None and self.__outcomeNumber.groupSize != None
    
  def getGroupSize(self):
    """ return the size of the treatment group or 0 if unknown"""
    gs = 0
    # if a group size was given with an outcome number, use it
    # otherwise, try to find the most relevant group size nearest the outcome number    
    if self.__outcomeNumber != None:
      gs = self.__outcomeNumber.getGroupSize()
    elif self.__eventRate != None:
      gs = self.__eventRate.getGroupSize()
    
    # find group size associated with the group
#    if gs < 1 and self.__group != None:
#      gs = self.__group.getSize(timeTemplate=self.__time) 
      
    # otherwise try to estimate the group size  
    if gs < 1 and self.__outcomeNumber != None and self.__eventRate != None \
      and self.eventRate() > 0:
      # we can estimate group size from ON and ER
      gs = float(int(10*self.getOutcomes()/self.eventRate()))/10
    return gs
    

  def eventRateString(self):
    """ return a formatted string containing the event rate """
    er = self.eventRate()
    if er == None:
      return '---'
    else:
      return '%.1f%%' % (100*self.eventRate())
    
#     if self.isComplete():
#       return '%.1f%%' % (100*self.eventRate())
#     else:
#       return ''

  def isComplete(self):
    """ return true if this template has all of the info it needs to be used """
    return self.__outcome != None and self.__group != None \
       and self.eventRate() != None

#           and ((self.__outcomeNumber != None and self.getGroupSize() > 0)\
#             or (self.__outcomeNumber != None and self.getOutcomes() == 0) \
#             or self.__eventRate != None)
 
  def getOutcomes(self):
    """ return the number of bad outcomes or -1 if non specified """
    if self.__outcomeNumber == None:
      return -1
    else:
      return self.__outcomeNumber.getOutcomes()  
  
       
  def statisticString(self, displayProb=False):
    """ return a string containing outcome statistics """
    if self.getOutcomes() >= 0:
      onStr =  str(self.getOutcomes()) 
    else:
      onStr = '---' 
    if self.getGroupSize() > 0:
      gStr = str(self.getGroupSize())
    else:
      gStr = '---'
    erStr = self.eventRateString() + ' (' + onStr+ '/' + gStr + '),'

    if displayProb:  
      associationProbStr = ''
      if self.__outcomeNumber != None:
        associationProbStr += ', on-outcome: ' + str(self.__outcomeNumber.outcomeProb) \
            + ', on-group: ' + str(self.__outcomeNumber.groupProb)
      if self.__eventRate != None:
        associationProbStr += ', er-outcome: ' + str(self.__eventRate.outcomeProb) \
            + ', er-group: ' + str(self.__eventRate.groupProb)
      
      erStr +=  ' (score = ' \
             + '%.2f' % self.getConfidence() + associationProbStr+')'  
           
    return erStr 
  
  def display(self):
    """ Write contents of outcome measurement to standard output."""
    self.write(sys.stdout) 
     
  def write(self, out):
    """ write template info to file """
    out.write('Outcome: ')
    if self.getOutcome() != None:
      out.write(self.getOutcome().name)
    else:
      out.write('---')

    out.write(', Group: ')
    if self.getGroup() != None:
      out.write(self.getGroup().name)

    out.write(', Time: ')
    if self.getTime() != None:
      out.write(self.getTime().name)
      
    out.write(', '+self.statisticString())      
    out.write('\n')   