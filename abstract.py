#!/usr/bin/python
# author: Rodney Summerscales
# contents: Classes for storing/managing abstracts and their contents

import sys
import os.path
import glob
import gc

from operator import attrgetter 
#import nltk
import re
import xml.dom
from xml.dom import minidom
from xml.dom.minidom import Document
from crossvalidate import CrossValidationSets
import xmlutil
from sentence import Sentence
from templates import Templates

def parseSentences(node, abstract=None):
  """ return a list of sentences elements constructed from an xml element
      that contain sentence elements """
  sList = []      
  sNodes = node.getElementsByTagName('sentence')
  for i in range(0, len(sNodes)):
    s = Sentence()
    s.parseXML(sNodes[i], i, abstract)
    if len(s.tokens) > 3:
      sList.append(s)
  return sList

def createSentenceListNode(name, sentenceList, doc):
  """ given a list of sentences, create an xml node with the given name, with
      the given list of sentences """
  node = doc.createElement(name)
  for s in sentenceList:
    node.appendChild(s.getXML(doc))
  return node

##############################################################
# Information for clinical report
##############################################################

class ReportEntry:
  """ A text block for an entry in a trial registry """
  sentences = None
  name = None
  
  def __init__(self, node):
    """ create a list of sentences given an XML node containing a list of sentence
        elements """
    self.name = xmlutil.getNodeTagName(node)
    self.sentences = parseSentences(node)

  def getXML(self, doc):
    """ return an xml node with information for this entity """
    return createSentenceListNode(self.name, self.sentences, doc)
   
class Intervention:
  name = None
  description = None
  
  """ Intervention information from a trial registry """
  def __init__(self, node):
    self.name = []
    self.description = []
    nodes = node.getElementsByTagName('name')
    if len(nodes) > 0:
      self.name = parseSentences(nodes[0])
    nodes = node.getElementsByTagName('description')
    if len(nodes) > 0:
      self.description = parseSentences(nodes[0])

  def getXML(self, doc):
    node = doc.createElement('intervention')
        
    if len(self.name) > 0:
      node.appendChild(createSentenceListNode('name', self.name, doc))
    if len(self.description) > 0:
      node.appendChild(createSentenceListNode('description', self.description, doc))
    return node
  
class Outcome:
  """ Outcome information from a trial registry """
  primary = False
  name = None
  times = None
  description = None
  
  def __init__(self, node):
    self.name = []
    self.times = []
    self.description = []
    primaryStr = node.getAttribute('primary')
    if primaryStr != None and primaryStr.lower() == 'true':
      self.primary = True
    else:
      self.primary = False
    nodes = node.getElementsByTagName('name')
    if len(nodes) > 0:
      self.name = parseSentences(nodes[0])
    nodes = node.getElementsByTagName('description')
    if len(nodes) > 0:
      self.description = parseSentences(nodes[0])
    nodes = node.getElementsByTagName('times')
    if len(nodes) > 0:
      self.times = parseSentences(nodes[0])
        
  def getXML(self, doc):
    node = doc.createElement('outcome')
    if self.primary:
      node.setAttribute('primary', 'true')
    else:
      node.setAttribute('primary', 'false')
        
    if len(self.name) > 0:
      node.appendChild(createSentenceListNode('name', self.name, doc))
    if len(self.description) > 0:
      node.appendChild(createSentenceListNode('description', self.description, doc))
    if len(self.times) > 0:
      node.appendChild(createSentenceListNode('times', self.times, doc))
    return node


class Report:
  """ Data from a NCT report. """
  id = ''
  gender = ''
  minAge = ''
  maxAge = ''
  locations = None
  conditions = None
  eligibilityCriteria = None
  inclusionCriteria = None
  exclusionCriteria = None
  interventions = None
  outcomes = None
  
  def __init__(self, node):
    self.id = xmlutil.getTextFromNodeCalled('id', node)
    self.gender = xmlutil.getTextFromNodeCalled('gender', node)
    self.minAge = xmlutil.getTextFromNodeCalled('minAge', node)
    self.maxAge = xmlutil.getTextFromNodeCalled('maxAge', node)
    
    self.locations = []
    lcNodes = node.getElementsByTagName('location_countries')
    if len(lcNodes) > 0:
      cNodes = lcNodes[0].getElementsByTagName('country')
      for countryNode in cNodes:
        self.locations.append(xmlutil.getText(countryNode))
        
    self.conditions = []
    cNodes = node.getElementsByTagName('condition')
    for cNode in cNodes:
      self.conditions.append(ReportEntry(cNode))
      
    self.eligibilityCriteria = []
    ecNodes = node.getElementsByTagName('eligibility')
    if len(ecNodes) > 0:
      cNodes = ecNodes[0].getElementsByTagName('criteria')
      for cNode in cNodes:
        self.eligibilityCriteria.append(ReportEntry(cNode))
           
    self.inclusionCriteria = []
    icNodes = node.getElementsByTagName('inclusion')
    if len(icNodes) > 0:
      cNodes = icNodes[0].getElementsByTagName('criteria')
      for cNode in cNodes:
        self.inclusionCriteria.append(ReportEntry(cNode))
    
    self.exclusionCriteria = []
    ecNodes = node.getElementsByTagName('exclusion')
    if len(ecNodes) > 0:
      cNodes = ecNodes[0].getElementsByTagName('criteria')
      for cNode in cNodes:
        self.exclusionCriteria.append(ReportEntry(cNode))
  
    self.interventions = []
    iNodes = node.getElementsByTagName('intervention')
    for iNode in iNodes:
      self.interventions.append(Intervention(iNode))
      
    self.outcomes = []
    oNodes = node.getElementsByTagName('outcome')
    for oNode in oNodes:
      self.outcomes.append(Outcome(oNode))
          
    
  def getXML(self, doc):
    """ return an xml element containing information for a clinical report element"""
    node = doc.createElement('report')
    node.appendChild(xmlutil.createNodeWithTextChild(doc, 'id', self.id))
    node.appendChild(xmlutil.createNodeWithTextChild(doc, 'gender', self.gender))
    node.appendChild(xmlutil.createNodeWithTextChild(doc, 'minAge', self.minAge))
    node.appendChild(xmlutil.createNodeWithTextChild(doc, 'maxAge', self.maxAge))
        
    if len(self.locations) > 0:
      lcNode = doc.createElement('location_countries')
      node.appendChild(lcNode)
      for country in self.locations:
        lcNode.appendChild(xmlutil.createNodeWithTextChild(doc, 'country', country))
      
    for condition in self.conditions:
      node.appendChild(condition.getXML(doc))

    if len(self.eligibilityCriteria) > 0:
      ecNode = doc.createElement('eligibility')
      node.appendChild(ecNode)
      for ec in self.eligibilityCriteria:
        ecNode.appendChild(ec.getXML(doc))

    if len(self.inclusionCriteria) > 0:
      icNode = doc.createElement('inclusion')
      node.appendChild(icNode)
      for ic in self.inclusionCriteria:
        icNode.appendChild(ic.getXML(doc))

    if len(self.exclusionCriteria) > 0:
      ecNode = doc.createElement('exclusion')
      node.appendChild(ecNode)
      for ec in self.exclusionCriteria:
        ecNode.appendChild(ec.getXML(doc))
        
    for intervention in self.interventions:
      node.appendChild(intervention.getXML(doc))

    for outcome in self.outcomes:
      node.appendChild(outcome.getXML(doc))
      
    return node
  

##############################################################
# List of Mesh terms for a document
##############################################################
class MeshTopic:
  """ a descriptor or qualifier mesh topic term """
  name = None
  majorTopic = False
  
  def __init__(self, node):
    self.name = xmlutil.getText(node)
    self.majorTopic = node.getAttribute('MajorTopicYN') == 'Y'
    
  def getXML(self, doc, tagName):
    """ return an xml element containing descriptor/qualifier information
        tagName = DescriptorName or QualifierName """
    node = xmlutil.createNodeWithTextChild(doc, tagName, self.name)
    if self.majorTopic:
      topicValue = 'Y'
    else:
      topicValue = 'N'
    node.setAttribute('MajorTopicYN', topicValue)
    return node
        
class MeshHeading:
  """ A topic and optional list of qualifier topics """
  descriptorName = None
  qualifierList = None
  
  def __init__(self, node):
    """ create a new mesh topic given a MeshHeading element """
    dNodeList = node.getElementsByTagName('DescriptorName')
    self.descriptorName = MeshTopic(dNodeList[0])
    
    qNodeList = node.getElementsByTagName('QualifierName')
    self.qualifierList = []
    for qNode in qNodeList:
      self.qualifierList.append(MeshTopic(qNode))
      
  def getXML(self, doc):
    """ return an xml element containing information for a MeshHeading element"""
    node = doc.createElement('MeshHeading')
    node.appendChild(self.descriptorName.getXML(doc, 'DescriptorName'))
    for qualifierName in self.qualifierList:
      node.appendChild(qualifierName.getXML(doc, 'QualifierName'))
    return node
      
    
class MeshHeadingList(list):
  """ Manage a list of mesh terms for an abstract """
  
  def __init__(self, node):
    """ create a new list of mesh terms given an xml node for a MeshHeadingList """
    nodeList = node.getElementsByTagName('MeshHeading')
    for node in nodeList:
      self.append(MeshHeading(node))
      
  def getXML(self, doc):
    """ create an xml element containing the entire list of mesh headings """
    node = doc.createElement('MeshHeadingList')
    for meshHeading in self:
      node.appendChild(meshHeading.getXML(doc))
    return node
    
    
##############################################################
# store an abstract
##############################################################
class Abstract:
  """ Read/write an abstract from an XML file. """
  id=''
  sentences=None
  __allSentences=None
  nIntegers = 0
  keyTermLists = None
  entities = None
  annotatedEntities = None
  summaryStats = None
  trueSummaryStats = None
  meshHeadingList = None
  __tokenSet = None            # set of all tokens in the abstract
  titleSentences = None
  affiliationSentences = None
  report = None
  acronyms = None
  
  def __init__(self, filename=None, sentenceFilter=None, loadRegistries=True):
    """ create a new abstract object
      filename = name of xml file containing abstract (optional)
      sentenceFilter = function that takes a Sentence object as a parameter
               and returns True if the sentence should be included 
               and False if it should be ignored.
               (optional. default is to include every sentence.)
      """
    self.id = ''
    self.sentences = []           # filtered sentence list
    self.__allSentences = []
    self.titleSentences = []
    self.affiliationSentences = []
    self.report = None
    self.nIntegers = 0
    self.keyTermLists = None
    self.entities = None
    self.annotatedEntities = None
    self.summaryStats = None
    self.trueSummaryStats = None
    self.meshHeadingList = None
    self.acronyms = {}
    if sentenceFilter == None:
      sentenceFilter = lambda sentence: True
    if filename != None:
      self.loadXML(filename, sentenceFilter, loadRegistries)
    self.__tokenSet = set([])
    self.__lemmaSet = set([])
    
  def loadXML(self, filename, sentenceFilter, loadRegistries):
    """ read an xml file containing an abstract """
    xmldoc = minidom.parse(filename)
    absNodes = xmldoc.getElementsByTagName('abstract')
    xmlutil.normalizeXMLTree(absNodes[0])

    self.id = absNodes[0].getAttribute('id')

    # read title
    nodes = absNodes[0].getElementsByTagName('title')
    if len(nodes) > 0:
      self.titleSentences = parseSentences(nodes[0], self)

    # read affiliation
    nodes = absNodes[0].getElementsByTagName('affiliation')
    if len(nodes) > 0:
      self.affiliationSentences = parseSentences(nodes[0], self)
  
    # read abstract body text
    nodes = absNodes[0].getElementsByTagName('body')
    if len(nodes) > 0:
      self.__allSentences = parseSentences(nodes[0], self)
      for s in self.__allSentences:
        if sentenceFilter(s) == True:
          self.sentences.append(s) 
    
    # read reports
    if loadRegistries:
      nodes = absNodes[0].getElementsByTagName('report')
      if len(nodes) > 0:
        self.report = Report(nodes[0])
        
#     meshNodes = absNodes[0].getElementsByTagName('MeshHeadingList')
#     if meshNodes != None and len(meshNodes) > 0:
#       self.meshHeadingList = MeshHeadingList(meshNodes[0])
    self.__buildAcronymTable()
    
  def __buildAcronymTable(self):
    """ look for acronym definitions in each abstract and build a table of acronyms
         and their expansions """
    for sentence in self.allSentences():
      for token in sentence:  
        if token.isAcronym() and token.text not in self.acronyms \
          and token.previousToken() != None and token.previousToken().text == '-LRB-' \
          and token.nextToken() != None and token.nextToken().text == '-RRB-':
          # found a new acronym definitions  (e.g.   ".... ( ACRONYM )...")
          # determine its expansion.
          # assume the definition is in the same sentence, to the left of the acronym
          prevToken = token.previousToken().previousToken()
          if prevToken != None and token.isValueAcronym() == False:
#          if prevToken != None:
            # first try the "first letter" approach
            # check if the first letter of each word up to the acronym
            # spell out the acronym
            i = len(token.text) - 1
            expansion = []
            pToken = prevToken
            ppToken = pToken.previousToken()
            tokensMatchAcronym = True
            while i >= 0 and pToken != None and tokensMatchAcronym:
              if token.text[i].lower() != pToken.text[0].lower():
                # if first letter in this token does not match, 
                # the current letter in the acronym, try the token before it   
                expansion.append(pToken)
                pToken = pToken.previousToken()
                
              if pToken != None and token.text[i].lower() == pToken.text[0].lower():       
                expansion.append(pToken)
                pToken = pToken.previousToken()  
                i -= 1
              else:
                tokensMatchAcronym = False
              
            if i < 0:
              expansion.reverse()
            else:
#              print i, token.text, pToken.text, token.text[i].lower(), pToken.text[0].lower() 
              expansion = []
           
#             if i >= 0:
#               # first letter approach failed
#               # use the words in the phrase containing the word just before the acronym
#               expansion = []
#               parent = prevToken.parseTreeNode.parent  
#               npNodes = parent.tokenNodes()
#               parenToken = token.previousToken()
#               for node in npNodes:
#                 if node.token == parenToken:
#                   break   # stop when we get to the acronymn  
#                 expansion.append(node.token)
            
            if len(expansion) > 0:
              self.acronyms[token.text] = expansion
              print token.text, '=',
              for t in expansion:
                print t.text,
              print
        

  def allSentences(self):
    """ return list of all sentences in abstract, regardless of current sentence filter """
    return self.__allSentences
     
  def filterSentences(self, sentenceFilter):
    """ apply a given filter to determine which sentences are included in the 
        main sentence list (sentence). 

        Filter is applied to entire collection of sentences, not the results
        from a previous filter operation."""
    self.sentences = []
    for s in self.__allSentences:
      if sentenceFilter(s) == True:
        self.sentences.append(s)
        
  def getTokenSet(self):
    """ return the set of tokens contained in this abstract """
    if len(self.__tokenSet) > 0:
      return self.__tokenSet     # token set already computed, just return it
      
    for sentence in self.sentences:
      for token in sentence:
        self.__tokenSet.add(token.text)
    
    return self.__tokenSet
        
  def getLemmaSet(self):
    """ return the set of lemmas contained in this abstract """
    if len(self.__lemmaSet) > 0:
      return self.__lemmaSet     # token set already computed, just return it

    for sentence in self.sentences:
      for token in sentence:
        self.__lemmaSet.add(token.lemma)
    
    return self.__lemmaSet


  def getXML(self, doc):
    """ return xml element containing the abstract """
    node = doc.createElement('abstract')
    node.setAttribute('id', self.id)
    
    if len(self.titleSentences) > 0:
      tNode = createSentenceListNode('title', self.titleSentences, doc)
      node.appendChild(tNode)
    
    if len(self.affiliationSentences) > 0:
      aNode = createSentenceListNode('affiliation', self.affiliationSentences, doc)
      node.appendChild(aNode)

    if len(self.__allSentences) > 0:
      bNode = createSentenceListNode('body', self.__allSentences, doc)
      node.appendChild(bNode)

    if self.report != None:
      node.appendChild(self.report.getXML(doc))
    
    if self.meshHeadingList != None:
      node.appendChild(self.meshHeadingList.getXML(doc))
    return node
  
  def writeXML(self, filename):
    """ write abstract out to xml file with given filename """
    print 'Writing:', filename
    doc = Document()
    node = self.getXML(doc)  
    out = open(filename, 'w')
    out.write('<?xml version="1.0" encoding="utf-8"?>\n')    
    out.write('<?xml-stylesheet href="abstract.xsl" type="text/xsl"?>\n')
    xmlutil.writexml(node, out)
    out.close()
    
  def writeHTML(self, out, labelList=[], showError=True):
    """ write sentences in html to output stream. 
        highlight correct and incorrect tokens 
        of a given label type (e.g. group, outcome number).
        supports up to 7 label types. colors for label types are (in order):
        
        blue, green, purple, darkorange, darkcyan, maroon, brown
        
        if more than 7 types are specified, all types are just blue.
        tokens with incorrect labels are colored red.
                
        If no labels are specified, all text is black.
    """
    colors = ['blue', 'green', 'purple', 'darkorange', 'darkcyan', \
              'maroon', 'brown']
    incorrectColor = 'red'
    correctColor = {}

    if len(labelList) == 0:
      useColors = False  # all text is black
    else:
      useColors = True
      if len(labelList) <= len(colors):
        i = 0
        for label in labelList:
          correctColor[label] = colors[i]  
          i += 1
      else:
        for label in labelList:
          correctColor[label] = 'blue'

    for sentence in self.sentences:
      out.write('<br> ')
      for token in sentence:
        tokenColor = 'black'
        comment = ''
        text = token.getDisplayText()
        if useColors:
          for label in labelList:
            if (showError == False and token.hasLabel(label) == True) \
              or (token.hasAnnotation(label) == True and token.hasLabel(label) == True):
              tokenColor = correctColor[label]
            elif showError == True and token.hasAnnotation(label) == True:
              # false negative
  #            tokenColor = 'red'
  #            comment = '_FN_'+label[0:2]
              tokenColor = correctColor[label]
              text = '<del>'+text+'</del>'
              break
            elif showError == True and token.hasLabel(label) == True:
              # false positive
              tokenColor = 'red'
  #            comment = '_FP_'+label[0:2]
              text += '_'+label[0:2]
              break
            
          out.write(' <span style=\"color:'+tokenColor+'\">')
          out.write(text)
          out.write('</span>')
        else:
          out.write(text)      
        out.write(' ')
      out.write('\n')
#      out.write('<br>'+sentence.parseString+'\n')
 
  def isKeyTerm(self, token):
    if self.keyTermLists != None:
      return self.keyTermLists.isKeyTerm(token, self)
    else:
      return False
      
  def isKeyBigram(self, token1, token2):
    if self.keyTermLists != None:
      return self.keyTermLists.isKeyBigram(token1, token2, self)
    else:
      return False  

  def isKeyTrigram(self, token1, token2, token3):
    if self.keyTermLists != None:
      return self.keyTermLists.isKeyTrigram(token1, token2, token3, self)
    else:
      return False

##############################################################
# maintain lists of abstracts
##############################################################
class AbstractList:
  """ maintain a list of Abstract objects """
  __list = []       # list of abstracts
  __index = 0       # current index into list of abstracts (used by iterator)
  cvSets = []       # list of testing/training sets for k-fold crossvalidation
  nFolds = 0      # number of folds used for crossvalidation
  sentenceFilter = None 
  
  def __init__(self, path=None, nFolds=0, sentenceFilter=None, label='', \
     loadRegistries=True):
    """ create new list of abstracts
        allow list to be populated from an xml file 
        
        path = directory containing xml files
        nFolds = number of folds used for cross-validation 
        sentenceFilter = function that takes a Sentence object as a parameter
                 and returns True if the sentence should be included 
                 and False if it should be ignored.
                 (optional. default is to include every sentence.)
                         """
    self.__list = []
    self.__index = 0
    self.cvSets = []
    self.nFolds = nFolds
    if sentenceFilter == None:
      self.sentenceFilter = lambda sentence: True
    else:
      self.sentenceFilter = sentenceFilter
    
    # read list of abstracts from file (if given)
    if path != None:
      self.readXML(path, label, loadRegistries)
    
    # create testing/training sets  
    self.createCrossValidationSets(nFolds)
  
  def copyList(self, absList):
    """ copy list of abstracts from given abstract list """
    self.__list = []
    for abstract in absList:
      self.__list.append(abstract)  
      
  def createCrossValidationSets(self, nFolds, randomSeed=42):
    """ create new crossvalidation sets """
    if nFolds > 1:      
      self.nFolds = nFolds
      self.cvSets = CrossValidationSets(self.__list, self.nFolds, randomSeed)
      print 'Abstract list built'
      print len(self.__list), 'abstracts'
      print 'Crossvalidation sets'
      for dataSet in self.cvSets:
        print 'Training:', len(dataSet.train), '\tTesting:', len(dataSet.test)
      self.sort()
    
  def sort(self):
    """ sort the list of abstracts by pubmed id """
    self.__list = sorted(self.__list, key=attrgetter('id'))
  
  def remove(self, abstract):
    """ remove a given abstract from list of abstracts """
    if abstract in self.__list:
      self.__list.remove(abstract)
             
  def applySentenceFilter(self, sentenceFilter):
    """ apply a given filter to determine which sentences are included in the 
        main sentence list (Abstract.sentence) for each abstract. 

        Filter is applied to entire collection of sentences, not the results
        from a previous filter operation."""
    for abs in self.__list:
      abs.filterSentences(sentenceFilter)

  def labelsToAnnotations(self, labelList):
    """ For each token in the list of abstracts, if it has been assigned a label in
        a given list of labels, change the label into an annotation for the token"""
    for abs in self.__list:
      for sentence in abs.allSentences():
        for token in sentence:
          for label in labelList:
            if token.hasAnnotation(label):
              token.removeAnnotation(label)
            if token.hasLabel(label):
              token.convertLabelToAnnotation(label)
#              token.setAnnotationAttribute(label, 'new', 'true')

  def labelsToSemanticTag(self, labelList):
    """ For each token in the list of abstracts, if it has been assigned a label in
        a given list of labels, change the label into a semantic tag for the token"""
    for abs in self.__list:
      for sentence in abs.sentences:
        for token in sentence:
          for label in labelList:
            if token.hasLabel(label):
              token.removeLabel(label)
              token.addSemanticTag(label)
            
  def cleanupAnnotations(self):
    """ Cleanup minor annotation inconsistencies in the current list of abstracts. """
    determinerSet = set(['a', 'the', 'an'])
    for abstract in self.__list:
      for sentence in abstract.allSentences():
        for token in sentence:
          nextToken = token.nextToken()
          if nextToken != None:
            # add determiner at beginning of mention if not already there
            if token.text in determinerSet:
              typeList = ['group', 'outcome']
              for type in typeList:              
                token.copyAnnotation(nextToken, type)
                
            if token.text == 'with':
              token.copyAnnotation(nextToken, 'condition')
              
  def removeLabels(self, labelList=[]):
    """ For each token in the list of abstracts, if it has been assigned a label in
        a given list of labels, remove it.
        if no list of labels is given, remove all labels. """    
    for abstract in self.__list:
      for sentence in abstract.allSentences():
        sentence.templates = None 
        sentence.annotatedTemplates = None
        for token in sentence:
          token.removeAllLabels(labelList)
  
  def createTemplates(self, useLabels=True):
    """ create mention and number templates for entity in each sentence in the list of abstracts 
        if useLabels is True, then detected mentions and numbers are used for templates
        otherwise use annotated information.
        
        this also creates annotated templates regardless. """
    for abstract in self.__list:
      for sentence in abstract.sentences:
        sentence.templates = Templates(sentence, useLabels=useLabels)
        sentence.annotatedTemplates = Templates(sentence, useLabels=False)
  
  def readXML(self, path='', label='', loadRegistries=True):
    """ read all xml files in a given directory """
    if len(path) > 0 and path[-1] != '/':
      path = path + '/'

    self.__list = []
    
    # get list of xml files in given directory
    if len(label) > 0:
      fileList = glob.glob(path+'*.'+label+'.xml')
    else:
      fileList = glob.glob(path+'*.xml')
      
    print 'Reading files from', path  
    for file in fileList:
      print 'Reading:',file
      self.__list.append(Abstract(file, self.sentenceFilter, loadRegistries))
    print 'Done!'
    gc.collect()
    self.cleanupAnnotations()
  
    
  def writeHTML(self, filename, labelList=[]):
    """ write sentences to html file. highlight correct and incorrect tokens 
        of a given label type (e.g. group, outcome number).
        supports up to 7 label types. colors for label types are (in order):
        
        blue, green, purple, darkorange, darkcyan, maroon, brown
        
        if more than 7 types are specified, all types are just blue.
        tokens with incorrect labels are colored red. 
        
        If no labels are specified, all text is black.
        """

    out = open(filename, mode='w')
    out.write("<html><head><title>" + filename + "</title><body>\n<p>")
    for abs in self.__list:
      out.write('<p><b><u>' + abs.id + ':</u></b></p>\n')
      abs.writeHTML(out, labelList)

    out.write('</body></html>\n')
    out.close()
    
  def writeXML(self, path='', label=''):
    """ write all abstracts to xml files in the given path
        abstract names are "<ABS_ID>.<LABEL>.xml" """
    if len(path) > 0 and path[-1] != '/':
      path = path + '/'
    for abs in self.__list:
      filename = path+abs.id
      if len(label) > 0:
        filename = filename+'.'+label
      filename = filename+'.xml'
      abs.writeXML(filename)
    gc.collect()
    
  def __len__(self):
    """ implement len() method """
    return len(self.__list)
  
  def __getitem__(self, index):
    return self.__list[index]

  def __setitem__(self, index, value):
    self.__list[index] = value
        
  # routines needed for implementing the iterator      
  def __iter__(self):
    self.__index = 0
    return self
    
  def next(self):
    if self.__index == len(self.__list):
      raise StopIteration
    self.__index = self.__index + 1
    return self.__list[self.__index-1]
    
    