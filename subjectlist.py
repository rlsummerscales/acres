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
from templates import createMergedList, createAnnotatedMergedList, countMatches
from entities import Entities
from textevaluationform import getIndent, bullet, evaluationPrompt, writeEvaluationElement, writeElementsMissing
from demographicelements import AgeInfo, LocationList, Gender

class SubjectList:
  """ Maintain list of treatment groups and common medical conditions
      for a given abstract. """
  groupTemplates = None     # list of group templates for the abstract
  ageInfo = None            # information describing age ranges of subjects
  ageTemplates = None
  conditionTemplates = None # list of templates describing common conditions
  populationTemplates = None
  abstract = None
  gender = None
  useTrialReports = None
  nTrueGroups = 0
  nTrueConditions = 0
  nTrueGroupSizes = 0
  
  def __init__(self, abstract, useAnnotated=False, useTrialReports=True):
    """ create a list of groups and common medical conditions given 
        an abstact object. """
    self.abstract = abstract
    self.useTrialReports = useTrialReports
    self.nTrueGroups = 0
    self.nTrueConditions = 0
    self.nTrueGroupSizes = 0

    if useAnnotated == True:
      self.groupTemplates = abstract.annotatedEntities.getList('group')
      self.ageTemplates = createAnnotatedMergedList(abstract, 'age')
      self.conditionTemplates = abstract.annotatedEntities.getList('condition')
      populationTemplates = createAnnotatedMergedList(abstract, 'population')
    else:  
      self.groupTemplates = abstract.entities.getList('group')
      self.ageTemplates = createMergedList(abstract, 'age')
      self.conditionTemplates = abstract.entities.getList('condition')
      populationTemplates = createMergedList(abstract, 'population') 
           
    self.ageInfo = AgeInfo(self.ageTemplates, abstract, self.useTrialReports) 
    self.gender = Gender(populationTemplates, abstract, self.useTrialReports)
    
    
    # filter useless population terms
    self.populationTemplates = []
    for pTemplate in populationTemplates:
      if pTemplate.isInteresting() > 0:
        # term is informative, keep it
        self.populationTemplates.append(pTemplate)
  
  def computeStatistics(self, errorOut):
    """ Count RPF statistics for each unique AGE, CONDITION, POPULATION entity
        statOut = file stream for RPF stats for all parts of summarization system
        errorOut = file stream for TPs, FPs, FNs
        
        return hash of IRstats, one for each mention type, keyed by mention type
        """
    stats = {}
    self.nTrueGroupSizes = 0

    aAgeTemplates = createAnnotatedMergedList(self.abstract, 'age')
    errorOut.write('age:\n')
    stats['age'] = self.ageInfo.countAgeMatches(aAgeTemplates, errorOut)

    errorOut.write('condition:\n')          
    aConditionTemplates = self.abstract.annotatedEntities.getList('condition')
    stats['condition'] = countMatches(aConditionTemplates, \
                                     self.conditionTemplates, errorOut)
    errorOut.write('group:\n')          
    aGroupTemplates = self.abstract.annotatedEntities.getList('group')
    stats['group'] = countMatches(aGroupTemplates, self.groupTemplates, errorOut)

    self.nTrueConditions = len(aConditionTemplates)
    self.nTrueGroups = len(aGroupTemplates)

    errorOut.write('group size:\n') 
    gsStats = IRstats()
    gsFound = set([])
    for gTemplate in self.groupTemplates:
      gSize = gTemplate.getSize(maxSize=True)
      if gSize != 0:
        # look for group size match in sizes for annotated group 
        found = False
        if gTemplate.matchedTemplate != None:
          for trueGSize in gTemplate.matchedTemplate.sizes:
            if gSize == trueGSize.value:
              found = True
              break
                 
        if found:
          # group size is correct
          gsStats.incTP()        
          errorOut.write('  +TP: %s size = %d\n' % (gTemplate.name, gSize))
          gTemplate.groupSizeEvaluation.markCorrect()
          gsFound.add(gTemplate.matchedTemplate)
        else:
          # group size is incorrect
          gsStats.incFP()  
          errorOut.write('  -FP: %s size = %d\n' % (gTemplate.name, gSize))
          gTemplate.groupSizeEvaluation.markIncorrect()
    # look for false negatives
    for trueTemplate in aGroupTemplates:
      if trueTemplate not in gsFound and trueTemplate.matchedTemplate != None and trueTemplate.getSize() > 0:
        # there should be a group size for this group
        gsStats.incFN()  
        errorOut.write('  -FN: %s size = %d\n' % \
                (trueTemplate.name, trueTemplate.getSize()))
        
    
    stats['group size'] = gsStats
    self.nTrueGroupSizes = gsStats.tp + gsStats.fn
#     errorOut.write('population:\n')
#     templates = createAnnotatedMergedList(self.abstract, 'population')
#     aPopulationTemplates = []
#     for pTemplate in templates:
#       if pTemplate.isInteresting() > 0:
#         # term is informative, keep it
#         aPopulationTemplates.append(pTemplate)
#     stats['population'] = self.countMatches(aPopulationTemplates, \
#                       self.populationTemplates, errorOut)
    return stats
    

      
  def getXML(self, doc, idPrefix):
    """ return an xml node that contains information about subjects
        in the study. """
#     if len(self.groupTemplates) == 0 and len(self.populationTemplates) == 0 \
#       and len(self.ageTemplates) == 0 and len(self.conditionTemplates) == 0:
#       return None
      
    subjectListNode = doc.createElement('Subjects')
    eligibilityNode = doc.createElement('Eligibility')
    subjectListNode.appendChild(eligibilityNode)
    
#     for pTemplate in self.populationTemplates:
#       popNode = doc.createElement('Population')
# #      setUMLSAttribute(popNode, pTemplate)
#       nameNode = xmlutil.createNodeWithTextChild(doc, 'Name', pTemplate.name)
#       popNode.appendChild(nameNode)
#       eligibilityNode.appendChild(popNode)
     
    eligibilityNode.appendChild(self.gender.getXML(doc, idPrefix)) 
    if len(self.ageInfo.ageValues) > 0:
      eligibilityNode.appendChild(self.ageInfo.getXML(doc, idPrefix))
      
    for cTemplate in self.conditionTemplates:
      cNode = doc.createElement('Criteria')
      cNode.setAttribute('source', 'abstract')
      id = idPrefix+cTemplate.id
      cTemplate.evaluation.id = id
      cNode.setAttribute('Id', id)
#      setUMLSAttribute(cNode, cTemplate)      
      nameNode = xmlutil.createNodeWithTextChild(doc, 'Name', cTemplate.name)
      cNode.appendChild(nameNode)
      type = 'unknown'
      firstToken = cTemplate.mention.tokens[0]
      if firstToken.text == 'with' or firstToken.lemma == 'have':
        type = 'inclusion'
      elif firstToken.text == 'without':
        type = 'exclusion'
      cNode.setAttribute('type', type)    
      eligibilityNode.appendChild(cNode)
    
    if self.useTrialReports and self.abstract.report != None:
      icCount = 0
      ecCount = 0
      for criteria in self.abstract.report.inclusionCriteria:
        cNode = doc.createElement('Criteria')
        cNode.setAttribute('source', 'trial_registry')
        cNode.setAttribute('Id', idPrefix+'ic'+str(icCount))
        icCount += 1
        text = criteria.sentences[0].toString() 
        for i in range(1, len(criteria.sentences)):
          text = text + ' ' + criteria.sentences[i].toString()
        nameNode = xmlutil.createNodeWithTextChild(doc, 'Name', text)
        cNode.appendChild(nameNode)
        cNode.setAttribute('type', 'inclusion')    
        eligibilityNode.appendChild(cNode)
      for criteria in self.abstract.report.exclusionCriteria:
        cNode = doc.createElement('Criteria')
        cNode.setAttribute('source', 'trial_registry')
        cNode.setAttribute('Id', idPrefix+'ec'+str(ecCount))
        ecCount += 1
        text = criteria.sentences[0].toString() 
        for i in range(1, len(criteria.sentences)):
          text = text + ' ' + criteria.sentences[i].toString()
        nameNode = xmlutil.createNodeWithTextChild(doc, 'Name', text)
        cNode.appendChild(nameNode)
        cNode.setAttribute('type', 'exclusion')    
        eligibilityNode.appendChild(cNode)
    
    for gTemplate in self.groupTemplates:
      groupNode = doc.createElement('Group')
      id = idPrefix+gTemplate.id
      gTemplate.evaluation.id = idPrefix+gTemplate.id
      groupNode.setAttribute('Id', id)
      groupNode.setAttribute('Role', gTemplate.role)
      gSize = gTemplate.getSize(maxSize=True)
      if gSize > 0:
        sNode = xmlutil.createNodeWithTextChild(doc, 'Size', str(gSize))
        id = idPrefix+gTemplate.id+'size'
        gTemplate.groupSizeEvaluation.id = id
        sNode.setAttribute('Id', id)
        groupNode.appendChild(sNode)
#      setUMLSAttribute(groupNode, gTemplate)      
      nameNode = xmlutil.createNodeWithTextChild(doc, 'Name', gTemplate.name)
      groupNode.appendChild(nameNode)
      subjectListNode.appendChild(groupNode)
    return subjectListNode
    
  def writeHTML(self, out):
    """ write subject list information to given output stream in html format. """
    out.write('<h3>Subjects</h3>\n')
#     out.write('<b>Population:</b><ul>\n')
#     for template in self.populationTemplates:
#       out.write('<li>'+template.name+'</li>')
#    out.write('</ul><b>Gender:</b><ul>\n')
#    out.write('<li>'+self.gender.value)
#    if self.gender.source != None:
#      out.write(' ('+self.gender.source+')')
#    out.write('</li></ul>\n')
    out.write('</ul><b>Age:</b><ul>\n')
    for type,av in self.ageInfo.ageValues.items():
      out.write('<li>'+av.type+': '+str(av.value)+' ')
      if av.units != None:
        out.write(av.units)
#      out.write(' ('+av.source+')</li>\n')
      out.write(' </li>\n')

    out.write('</ul>')
    out.write('</ul><b>Condition:</b><ul>\n')
    for template in self.conditionTemplates:
      out.write('<li>'+template.name+'</li>')
    out.write('</ul><b>Groups:</b><ul>\n')
    for template in self.groupTemplates:
      size = 'unknown'
      gSize = template.getSize(maxSize=True)
      if gSize > 0:
        size = str(gSize)
      out.write('<li>'+template.name+' (size=' + size + ')</li>')  
#      out.write('<li>'+template.name+' (id='+template.id+', role=' \
#                 +template.role+', size=' + size + ')</li>')

    out.write('</ul>\n')
 
  def writeEvaluationForm(self, out):    
    out.write('GENDER:\n\n')
    writeEvaluationElement(self.gender.value, out)
  
    out.write('AGE:\n\n')
    for type,av in self.ageInfo.ageValues.items():
      avString = av.type+': '+str(av.value)
      if av.units != None:
        avString += ' '+av.units
      writeEvaluationElement(avString, out)
    writeElementsMissing('ages', out)
 
    out.write('CONDITIONS:\n\n')
    for template in self.conditionTemplates:
      writeEvaluationElement(template.name, out)
    writeElementsMissing('conditions', out)
 
    out.write('GROUPS:\n\n')
    for template in self.groupTemplates:
      writeEvaluationElement(template.name, out)
      gSize = template.getSize(maxSize=True)      
      if gSize > 0:
        writeEvaluationElement('size: %d' % gSize, out, indentLevel=1)
    
    writeElementsMissing('groups', out)
   
