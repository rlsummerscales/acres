#!/usr/bin/python
# author: Rodney Summerscales

import sys
#import nltk
#from nltk.corpus import wordnet as wn

from abstract import AbstractList
from summary import SummaryList
from statlist import StatList

if len(sys.argv) < 2:
  print "Usage: corpusstats.py <INPUT_PATH>"
  print "Analyze the characteristics of all the files "
  print "in the directory specified by <INPUT_PATH>"
  print "using their annotated information."
  sys.exit()

#entityTypes = ['group', 'outcome', 'condition', 'age', 'threshold',\
#               'population', 'time', 'gs', 'on']
numberTypes = ['agevalue', 'gs', 'on', 'eventrate']
mentionTypes = ['age', 'condition','group', 'outcome']
entityTypes = numberTypes + mentionTypes

mentionCounts = {}
mentionLengths = {}
for type in entityTypes:
  mentionCounts[type] = 0
  mentionLengths[type] = 0
  
tokenCount = 0
acronymCounts = 0
structuredAbstracts = 0
sentenceCount = 0
nRegistries = 0
  
inputPath = sys.argv[1]
absList = AbstractList(inputPath)

numberCount = {}
binValues = [0, 1, 10, 20, 30, 40, 50, 100, 200]
for nType in numberTypes+['other']:
  numberCount[nType] = {}
  for bv in binValues:
    numberCount[nType][bv] = 0

groupRole = {}
sectionLabelCount = {}
for type in ['integer', 'percentage']+numberTypes+mentionTypes:
  sectionLabelCount[type] = {}
      
nWithValues = 0
nWithON = 0    
for abs in absList:
  nLabels = 0
  curLabel = ''
  groupRole[abs] = {'control':0, 'experiment':0, 'unknown':0}
  sentenceCount += len(abs.sentences)
  groupRoleAssignments = {'control':set([]), 'experiment':set([])}
  hasValues = False
  hasON = False
  
  for sentence in abs.sentences:
    for eType in sectionLabelCount.keys():
      if sentence.section not in sectionLabelCount[eType]:
        sectionLabelCount[eType][sentence.section] = 0 
  
  for sentence in abs.sentences:
    aList = sentence.getAnnotatedMentions('group')
    for m in aList:
      role = m.tokens[0].getAnnotationAttribute('group', 'role') 
      id = m.tokens[0].getAnnotationAttribute('group', 'id')
      if len(id) == 0:
        print '%s: ERROR - Group missing id annotation --> %s'% (abs.id, m.text)
      if role in set(['control', 'experiment']):
        groupRoleAssignments[role].add(id)
          
  for sentence in abs.sentences:
    if sentence.section != curLabel:
      curLabel = sentence.section
      nLabels += 1
    
    for mType in entityTypes: 
      aList = sentence.getAnnotatedMentions(mType)
      sectionLabelCount[mType][sentence.section] += len(aList)
      mentionCounts[mType] += len(aList)
      for m in aList:
        mentionLengths[mType] += len(m.tokens)
      
        if mType == 'group':
          id = m.tokens[0].getAnnotationAttribute('group', 'id')
          if id in groupRoleAssignments['control'] and id in groupRoleAssignments['experiment']:
            print '%s: ERROR - Group has BOTH roles --> %s'% (abs.id, m.text)
          elif id in groupRoleAssignments['control']:
            groupRole[abs]['control'] += 1
          elif id in groupRoleAssignments['experiment']:
            groupRole[abs]['experiment'] += 1
          else:
            groupRole[abs]['unknown'] += 1
            print '%s: Unknown role for group --> %s'%(abs.id, m.text)
        elif mType == 'eventrate' or mType == 'on':
          text = m.text.replace('%','')
          try:
            value = float(text)
            if value < 0:
              print abs.id, ' contains negative outcome measurement:', value
          except:
            print abs.id, ' contains non-numerals:', text
        elif mType == 'agevalue':
          print abs.id, 'AGE VALUE:', m.text

            
    for token in sentence:
      tokenCount += 1
      if token.isAcronym():
        acronymCounts += 1   
         
      if token.isImportantNumber():
        if token.isPercentage():
          sectionLabelCount['percentage'][sentence.section] += 1
        elif token.isInteger():
          sectionLabelCount['integer'][sentence.section] += 1
        nType = 'other'
        for type in numberTypes:
          if token.hasAnnotation(type):
            nType = type
            if nType != 'agevalue':
              hasValues = True
            if nType == 'on':
              hasON = True
            break
        value = token.getValue()
        for bv in binValues:
          if value < bv or bv == binValues[-1]:
            numberCount[nType][bv] += 1
#            print nType, value, '<', bv
            break
#  if hasON:
#    nWithON += 1
#  else:  
#    print abs.id, ' does not contain outcome number values'   
            
  if hasValues == True:
    nWithValues += 1  
  else:
    print abs.id, ' does not contain any values!!!'   
           
  if abs.report != None:
    nRegistries += 1
               
  if nLabels > 1:
    structuredAbstracts += 1

nControl = 0
nExperiment = 0
nUnknown = 0
nControlMissing = 0
nExperimentMissing = 0
for abstract in absList:
  nControl += groupRole[abstract]['control']
  nExperiment += groupRole[abstract]['experiment']
  nUnknown += groupRole[abstract]['unknown']
  if groupRole[abstract]['control'] == 0:
    print '%s: Missing Control group' % abstract.id
    nControlMissing += 1
  if groupRole[abstract]['experiment'] == 0:
    print '%s: Missing Experiment group' % abstract.id
    nExperimentMissing += 1

nAbstracts = len(absList)
print 'Number of Abstracts:', nAbstracts
print 'Abstracts with trial registries:', nRegistries
print 'Structured abstracts:', structuredAbstracts, 
print '  (%.2f)' % (float(structuredAbstracts)/nAbstracts)
print 'Avg token count: %.1f' % (float(tokenCount)/nAbstracts)
print 'Avg number of sentences: %0.1f' % (float(sentenceCount)/nAbstracts)
print 'Sentence length: %.1f' % (float(tokenCount)/sentenceCount)
print 'Avg number of acronym occurences: %0.1f' % (float(acronymCounts)/nAbstracts)
print 'Number of abstracts with values: %d (%.2f)' % (nWithValues, float(nWithValues)/nAbstracts)
print 'Number of abstracts with outcome numbers: %d (%.2f)' % (nWithON, float(nWithON)/nAbstracts)

print 'Number of Control groups:', nControl
print 'Number of Experiment groups:', nExperiment
print 'Number of Unknown groups:', nUnknown
print 'Number of abstracts missing control:', nControlMissing
print 'Number of abstracts missing experiment:', nExperimentMissing


print '\t total mentions   avg mentions   avg length'
for type in entityTypes:
  print type.ljust(15), mentionCounts[type],'\t\t',
  if mentionCounts[type] > 0: 
    print '%.1f' % (float(mentionCounts[type])/nAbstracts), 
    print '\t\t %.1f' % (float(mentionLengths[type])/mentionCounts[type])
  else:
    print 0.0, '\t\t', 0.0
    
statList = StatList()
summaryList = SummaryList(absList, statList, useAnnotated=True)


entityTypes = ['condition', 'group', 'outcome', 'ARR', 'ARR-computed-only',\
               'ARR-detected-only', 'ARR-mixed', 'ARR-both', 'ARR-ER-not-needed']
entityCounts = {}
for type in entityTypes:
  entityCounts[type] = 0
for summary in summaryList.list:
  entityCounts['condition'] += len(summary.subjectList.conditionTemplates)
  entityCounts['group'] += len(summary.subjectList.groupTemplates)
  entityCounts['outcome'] += len(summary.outcomeList.outcomeTemplates)
  for oTemplate in summary.outcomeList.outcomeTemplates:
    entityCounts['ARR'] += len(oTemplate.summaryStats)
    for sTemplate in oTemplate.summaryStats:
      # check for both computed and detected event rate

      # check for detected only
      if sTemplate.lessEffective.eventrateValueOnly() \
        and sTemplate.moreEffective.eventrateValueOnly():
        entityCounts['ARR-detected-only'] += 1
      # check for computed only
      elif sTemplate.lessEffective.calculatedEventRateOnly() \
        and sTemplate.moreEffective.calculatedEventRateOnly():
        entityCounts['ARR-computed-only'] += 1
      # there is a combination
      elif sTemplate.lessEffective.eventrateValueOnly() \
        or sTemplate.moreEffective.eventrateValueOnly() \
        or sTemplate.lessEffective.calculatedEventRateOnly() \
        or sTemplate.moreEffective.calculatedEventRateOnly():
        entityCounts['ARR-mixed'] += 1
        print '--- ARR mixed ---'
        sTemplate.write(sys.stdout)
      # there is redundancy 
      else:
        entityCounts['ARR-both'] += 1
      
      # detected event rates are not necessary
      if sTemplate.lessEffective.hasCalculatedEventRate() \
        and sTemplate.moreEffective.hasCalculatedEventRate():
        entityCounts['ARR-ER-not-needed'] += 1
      
    
print '\t total entities  avg entities  avg mentions in entity'
for type in entityTypes:
  print type.ljust(15), entityCounts[type],'\t\t',
  if entityCounts[type] > 0: 
    print '%.1f' % (float(entityCounts[type])/nAbstracts), 
    if type in mentionCounts:
      print '\t\t %.1f' % (float(mentionCounts[type])/entityCounts[type])
    else:
      print
  else:
    print 0.0, '\t\t', 0.0
  
print '\n\t\t',
for bv in binValues:
  print '<', bv, '\t',
print
  
for nType in numberCount:
  print nType.ljust(15),
  for bv in binValues:
    print numberCount[nType][bv],'\t',
  print 

for eType in sectionLabelCount.keys():
  print eType, ' section counts'
  for section, counts in sectionLabelCount[eType].items():
    print '\t %s: %d'%(section, counts)
  print


