#!/usr/bin/python
# author: Rodney Summerscales

import xmlutil
import templates
import sys
import time
import xml
import codecs
import math
import sentencefilters

from operator import itemgetter
from xml.dom.minidom import Document
from irstats import IRstats
from summarystats import SummaryStats
from abstract import AbstractList
from templates import Templates
from agetemplate import AgeValue
from templates import createMergedList, createAnnotatedMergedList
from entities import Entities
from textevaluationform import getIndent, bullet, evaluationPrompt, writeEvaluationElement, writeElementsMissing


class AgeInfo:
  """ information regarding the ages of the trial participants """
  ageValues = {}
  nTrueAgeValues = 0
  reportMin = None
  reportMax = None
  timeWords = set(['hours', 'day', 'days', 'week', 'weeks', 'month', 'months',\
                  'year', 'years']) 
  def __init__(self, ageTemplates, abstract, useTrialReports=True):
    self.ageValues = {}
    self.reportMin = None
    reportMax = None
    self.nTrueAgeValues = 0
    
    if useTrialReports and abstract.report != None:
      av = self.parseAgeValue(abstract.report.minAge)
      if av != None:
        av.type = 'min'
        self.ageValues[av.type] = av
      av = self.parseAgeValue(abstract.report.maxAge)
      if av != None:
        av.type = 'max'
        self.ageValues[av.type] = av

      # look for good values that match trial registry values
      discardTemplate = {}
      for template in ageTemplates:
        discardTemplate[template] = False
        goodValues = []
        for type in ['min', 'max']:
          if type in self.ageValues and type in template.values:
            if self.ageValues[type].ageInHours() == template.values[type].ageInHours():
              goodValues.append(template.values[type])
              template.values[type].matchesTrialRegistry = True
            else:
              discardTemplate[template] = True
              break
        for av in goodValues:
          self.ageValues[av.type] = av
      # discard all values in age phrases that disagree with trial registry ages
      for template,discard in discardTemplate.items():
        if discard:
          ageTemplates.remove(template)
                   
    # check to make sure there are no disagreements on values
    # that is, make sure we do not have different min ages or mean ages.
    detectedAgeValues = {}             
    discardAllValues = False    
    for template in ageTemplates:
      for type,av in template.values.items():
        if type not in detectedAgeValues:
          detectedAgeValues[av.type] = av
        else:
          newValue = av.ageInHours()
          oldValue = detectedAgeValues[av.type].ageInHours()
          if newValue != oldValue:
            # two age values of the same type, but different values
            # not sure which one is correct. Discard all age values for now
            discardAllValues = True
            break
    # make sure that the age values are consistent
    if 'min' in detectedAgeValues:
      minAge = detectedAgeValues['min'].ageInHours()
    else:      
      minAge = -1

    if 'max' in detectedAgeValues:
      maxAge = detectedAgeValues['max'].ageInHours()
    else:      
      maxAge = 999999 
  
    if minAge > maxAge:
      discardAllValues = True
    
    # if there is a mean or median check to make sure that they are between the min and max
    checkVals = []
    if 'mean' in detectedAgeValues:
      checkVals.append(detectedAgeValues['mean'].ageInHours())
    if 'median' in detectedAgeValues:
      checkVals.append(detectedAgeValues['median'].ageInHours())
    
    for val in checkVals:
      if val < minAge or val > maxAge:
        # this value is beyond the bounds of the min/max age
        # discard all values
        discardAllValues = True
        break
    
    if discardAllValues == False:
      # age values are unique and consistent
      for type,av in detectedAgeValues.items():
        self.ageValues[type] = av
      
      
      
  def parseAgeValue(self, text):
    """ convert an age value phrase of the form "<NUMBER> <TIME_UNITS>" to an 
        age value object or return None if unsuccessful """
    av = None
    tokens = text.split()
    value = None
    units = None
    for t in tokens:
      t = t.lower()
      if t.isdigit():
        value = t
      elif t in self.timeWords:
        units = t
    if value != None:
      av = AgeValue(source='trial_registry')
      av.value = int(value)
      av.units = units
    return av 
    
  def countAgeMatches(self, aAgeTemplates, errorOut):
    """ count the number of age value matches in a set of annotated age templates """
    annotatedAgeValues = {'min':set([]), 'max':set([]), 'mean':set([]), 'median':set([])}
    for template in aAgeTemplates:
      for type, avList in template.trueValues.items():
        for av in avList:
#          print '@@@ ADDING AGE VALUE:', type, av.value
#          if len(annotatedAgeValues[type]) > 0:
#            print '-- Redundant value'
          annotatedAgeValues[type].add(av)
    self.nTrueAgeValues = 0
    annotatedValueFound = {}
    for avSet in annotatedAgeValues.values():
      for av in avSet:
        annotatedValueFound[av] = False
        self.nTrueAgeValues += 1
    # count the number of detected values that match annotated ones
    stats = IRstats()
    for type, av in self.ageValues.items():
#      print '@@@ Checking:', type, av.value
      if av.source != 'trial_registry':
        foundAgeValue = False
        for annotatedValue in annotatedAgeValues[type]:          
          if av.value == annotatedValue.value:
            stats.incTP()
            errorOut.write('  +TP: %s = %d\n' % (type,av.value))
#            print '  +TP: %s = %d' % (type,av.value)
            annotatedValueFound[annotatedValue] = True
            av.evaluation.markCorrect()
            foundAgeValue = True
        if foundAgeValue == False:  
          stats.incFP()
          errorOut.write('  -FP: %s = %d\n' % (type, av.value))
#          print '  -FP: %s = %d' % (type, av.value)
          av.evaluation.markIncorrect()
#      else:
#        print '@@@@ AGE VALUE SOURCE IS TRIAL REGISTRY'
        
    # count the ones that we missed
    for av, found in annotatedValueFound.items():
      if found == False:
        stats.incFN()
        errorOut.write('  -FN: %s = %d\n' % (av.type, av.value))
#        print '  -FN: %s = %d' % (av.type, av.value)
           
    return stats
    
          
        
  def getXML(self, doc,idPrefix):
    """ return xml element containing all known age information about the population"""
    ageNode = doc.createElement('Age')
    avCount = 0
    for type,av in self.ageValues.items():
      avNode = av.getXML(doc)
      ageNode.appendChild(avNode)
      id = idPrefix+'av'+str(avCount)
      av.evaluation.id = id
      avNode.setAttribute('id', id)
      avCount += 1
    return ageNode
  

#----------------------------------------------------------------------    
  
class Gender:
  """ Gender of participants in the trial """
  value = None   # 'men', 'women', 'unknown'
  source = None
  maleWords = set(['male', 'males', 'men', 'man', 'boys', 'boy'])
  femaleWords = set(['female', 'females', 'woman', 'women', 'girls', 'girl'])
  
  def __init__(self, populationTemplates, abstract, useTrialReports=True):
    self.value = 'unknown'
    self.source = 'abstract'
    if useTrialReports and abstract.report != None and abstract.report.gender != None: 
      self.value = abstract.report.gender.lower() 
      self.source = 'trial_registry'
      if self.value != 'both':
        if self.value in self.maleWords:
          self.value = 'men'
        elif self.value in self.femaleWords:
          self.value = 'female'
    else:
      containsMen = False
      containsWomen = False
      for template in populationTemplates:
        pText = template.name.lower()
        if pText in self.maleWords:
          containsMen = True
        elif pText in self.femaleWords:
          containsWomen = True
      if containsMen == True and containsWomen == True:
        self.value = 'both'
      elif containsWomen == True:
        self.value = 'women'
      elif containsMen == True:
        self.value = 'men'
      if self.value != 'unknown':
        self.source = 'abstract'
        
  def getXML(self, doc, idPrefix):
    node = xmlutil.createNodeWithTextChild(doc, 'Gender', self.value)
    node.setAttribute('source', self.source)
    node.setAttribute('id', idPrefix+'gen0')
    return node
  
  
#----------------------------------------------------------------------  


class LocationList:
  """ create a list of locations where the study was performed. 
      Locations are determine using the following rules.
        1. If a NCT report exists, use the location countries from that.
        2. If the system has found any locations in the first half of the
           abstract, use that.
        3. Otherwise, use the location for the authors of the paper.
  """
  abstract = None
  locationTemplates = None
  locationStrings = None
  source = None
  
  def __init__(self, abstract, useTrialReports=True):
    """ build list of locations """
    self.abstract = abstract
    self.source = ''
    self.locationTemplates = []
    self.locationStrings = []

    if useTrialReports and self.abstract.report != None \
      and len(self.abstract.report.locations) > 0:
      for country in self.abstract.report.locations:
        self.locationStrings.append(country)
        self.source = 'trial_registry'
    else: 
      self.locationTemplates = createMergedList(abstract, 'location') 
      self.source = 'abstract'
      if len(self.locationTemplates) == 0 \
         and len(self.abstract.affiliationSentences) > 0:
        # use location in the affiliation section of the abstract
        self.source = 'affiliation'
        s = self.abstract.affiliationSentences[0]
        lastTokenIndex = len(s.tokens)-1
        if s.tokens[lastTokenIndex].text == '.':
          lastTokenIndex -= 1
        if lastTokenIndex > 0 and s.tokens[lastTokenIndex].isLocation():
          country = s.tokens[lastTokenIndex].text
          i = lastTokenIndex - 1
          while i >= 0 and s.tokens[i].text != ',':
            country = s.tokens[i].text + ' ' + country
            i -= 1
          self.locationStrings.append(country)
  
  def getXML(self, doc, idPrefix):
    """ return an xml node that contains information about the outcomes
        measured in the study. """
    locationList = self.getLocations()
    if len(locationList) == 0:
      return None
      
    locationListNode = doc.createElement('Locations')
    lCount = 0
    for location in locationList:
      locationNode = xmlutil.createNodeWithTextChild(doc, 'Location', location)
      locationNode.setAttribute('source', self.source)
      locationNode.setAttribute('id', idPrefix+'loc'+str(lCount))
      lCount += 1
#      setUMLSAttribute(nameNode, oTemplate)
      locationListNode.appendChild(locationNode)
    
    return locationListNode

  def getLocations(self):
    """ return list of strings containing countries where study took place """
    locations = []
    for template in self.locationTemplates:
      locations.append(template.name)
    for cString in self.locationStrings:
      locations.append(cString)
    return locations    
         
  def writeHTML(self, out):
    """ write outcome list information to given output stream in html format. """
    out.write('<h3>Locations</h3><ul>\n')
    out.write('<li>Source: '+self.source+'</li>\n')
    if self.source == 'affiliation':
      out.write('<li> affiliation: '+self.abstract.affiliationSentences[0].toString()+'</li>')
    out.write('<li>Countries: '+', '.join(self.getLocations())+'</li>\n</ul>\n')   

  def writeEvaluationForm(self, out):
    out.write('LOCATIONS:\n')

    if self.source != 'trial_registry':
      for location in self.getLocations():
        writeEvaluationElement(location, out)
    writeElementsMissing('locations', out)
  