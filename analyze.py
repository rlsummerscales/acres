#!/usr/bin/python
# author: Rodney Summerscales
# contents: analyze context of mentions and values for the purpose of 
# identifying good features for mention and value detection

import sys
#import nltk
#from nltk.corpus import wordnet as wn

from irstats import IRstats
from abstract import AbstractList
#from parsetree import ParseTreeNode
#from parsetree import SimplifiedTreeNode
import mallet

def writePatterns(patternOut, sentence):
  """ output results for given token patterns """
  for token in sentence:
    if token.specialValueType != None:
      s = ''
      for i in range(max(0, token.index-3), min(len(sentence), token.index+4)):
        
        if sentence[i] == token:
          s += ' ->'+sentence[i].text+'<- '
        else:          
          s += sentence[i].text+' '
      patternOut.write(('%60s' % s) + '-->  ' + token.specialValueType+'='+token.text+'\n')


def countUMLS(out, sentence, entityTypes, umlsTypeCounts):
  """ count the number of umls chunks that have a given set of labels vs. those that do not """
  sTypes = {}
  for chunk in sentence.umlsChunks:
    for cType in chunk.types:
      if cType not in umlsTypeCounts:
        umlsTypeCounts[cType] = {}
        umlsTypeCounts[cType]['tokens'] = 0
        for entityType in entityTypes:
          umlsTypeCounts[cType][entityType] = 0
    for i in range(chunk.startIdx, chunk.endIdx+1):
      if i not in sTypes:
        sTypes[i] = set([])
      for cType in chunk.types:
        sTypes[i].add(cType)
  
  for i in sTypes:
    token = sentence[i]
    for sType in sTypes[i]:
      umlsTypeCounts[sType]['tokens'] += 1
      for eType in entityTypes:
        if token.hasAnnotation(eType):
            umlsTypeCounts[sType][eType] += 1
                      
#     labelsAllTokensHave = [] 
#     labelsSomeToTokensHave = []
#     for cType in entityTypes:
#       containsLabel = False
#       missingLabel = False
# 
#       for i in range(chunk.startIdx, chunk.endIdx+1):
#         token = sentence[i]
#         if token.hasAnnotation(cType):
#           containsLabel = True
#         else:
#           missingLabel = True
#       if containsLabel == True and missingLabel == False:
#         labelsAllTokensHave.append(cType)
#       elif containsLabel:
#         labelsSomeTokensHave.append(cType)

def writeUMLSSentence(out, sentence):
  """ output sentence with umls chunks identified """
  if len(sentence.umlsChunks) == 0:
    return
  
  i = 0
  curChunk = sentence.umlsChunks[i]  
  for token in sentence:
    if token.index == curChunk.startIdx:
      out.write('[')
      
    out.write(token.text)
    
    if token.index == curChunk.endIdx:
      out.write('] ')
      i += 1
      if i < len(sentence.umlsChunks):
        curChunk = sentence.umlsChunks[i]
    else:
      out.write(' ')
  out.write('\n')    
              
def writeSubstitutedSentence(out, sentence, entityTypes):
  """ output sentence with entities of cType enitityType replaced with
      just a single token """
  currentType = None
#  specialTokens = set(['-LRB-','-RRB-',',','verses'])
  for token in sentence:
    if currentType != None and token.hasAnnotation(currentType) == False:
      # end of current entity
      currentType = None
    
    if currentType == None:
      # check if current token has an annotation that we are interested in
      for cType in entityTypes:
        if token.hasAnnotation(cType):
          currentType = cType
          out.write(currentType.upper() + ' ')

    if currentType == None and (token.pos[0:2] == 'VB'  \
       or token.pos == 'CC'):
      # not currently in an entity, output token
      out.write(token.text+' ')
    
#     if currentType == None and (token.pos[0:2] == 'VB' or token.pos[0:2] == 'IN' \
#        or token.pos == 'CC' or token.text in specialTokens):
#       # not currently in an entity, output token
#       out.write(token.text+' ')
#     elif token.isNumber():
#       out.write('NUM ')
#       
  out.write('\n')

def findPathToRoot(out, sentence, entityType, pathCounts):
  """ find the path from each word to a verb in the sentence. 
      record the path in pathCounts"""
  sentence.dependencyGraphBFS()
  depSet = set(['ccomp', 'xcomp', 'csubj', 'csubjpass', 'purpcl', 'xsubj'])
  for token in sentence:
    if token.hasAnnotation(entityType):
      depPath = ''
      depVerbPath = ''
      p = token.parent
      while p != None:
        depPath = p.type + '<-' + depPath
        print depPath
        if p.type in depSet:
          depVerbPath = p.type+'_'+p.token.text+'<-'+depVerbPath
        else:
          depVerbPath = p.type+'<-'+depVerbPath
        p = p.token.parent
      if len(depVerbPath) > 0:
        pathCounts[depVerbPath] = 1 + pathCounts.get(depVerbPath, 0)
      if len(depPath) > 0:        
        pathCounts[depPath] = 1 + pathCounts.get(depPath, 0)

        
def findKeyVerbs(out, sentence, entityType, verbCounts):
  """ find the closest parent verbs in parse tree containing mentions """
#  out.write('Parent verbs: ')
  inEntity = False
  for token in sentence:
    if token.hasAnnotation(entityType) == False:
      inEntity = False
    elif inEntity == False:
      inEntity = True
      closestVerb = token.parseTreeNode.closestParentVerbNode()
      if closestVerb != None:
#        out.write(closestVerb.text+' ')
        verbCounts[closestVerb.token.lemma] = 1 + verbCounts.get(closestVerb.token.lemma, 0) 
      else:
        verbCounts['---'] = 1 + verbCounts['---'] 
      
#  out.write('\n')
  
if len(sys.argv) < 3:
  print "Usage: analyze.py <TYPE> <INPUT_PATH>"
  print "Analyze the context of mentions of type <TYPE>"
  print "in of all files in the directory specified by <INPUT_PATH>"
  print "using their annotated information."
  print "Output is written to the file '<TYPE>.context.txt'" 
  sys.exit()

entityType = sys.argv[1]    
#entityTypes = ['group', 'outcome', 'condition', 'age', 'threshold',\
#               'population', 'time', 'gs', 'on']
entityTypes = ['group', 'outcome', 'condition', 'age', \
               'gs', 'on', 'eventrate', 'population']
entityTokenCounts = {}
for type in entityTypes:
  entityTokenCounts[type] = 0
  
inputPath = sys.argv[2]
contextOut = open(entityType+'.context.txt', 'w')
entityOut = open('entitysentences.txt', 'w')
patternOut = open('pattern.txt', 'w')
primaryOutcomeOut = open('primaryoutcome.txt', 'w')

absList = AbstractList(inputPath)

verbCounts = {}
verbCounts['---'] = 0
verbRuleCounts = {}
pathCounts = {}
primaryOutcomeSet = set(['outcome', 'end', 'endpoint'])
entityPhrases = 0
nounPhrases = 0
aCount = 0
numberSentenceCount = 0
nSentences = 0
sectionCounts = {}
nlmLabelCounts = {}
sentenceNumber = {}
nTotalSentences = 0
totalNumberSentenceCount = 0
totalSectionCounts = {}
totalNlmLabelCounts  = {}
totalSentenceNumber = {}

for abstract in absList:
  contextOut.write('--- '+abstract.id+' ---\n')
  entityOut.write('--- '+abstract.id+' ---\n')
  patternOut.write('--- '+abstract.id+' ---\n')
  primaryOutcomeOut.write('--- '+abstract.id+' ---\n')
  
#   for acronym, expansion in abstract.acronyms.items():
#     aCount += 1
#     primaryOutcomeOut.write('Acronym ('+str(aCount)+'): '+acronym+'\n')
#     primaryOutcomeOut.write('Expansion: ')
#     for token in expansion:            
#       primaryOutcomeOut.write(token.text+' ')
#     primaryOutcomeOut.write('\n\n')

  for sentence in abstract.sentences:
    writePatterns(patternOut, sentence)
    
    
    for token in sentence:
#       closestVerb = token.parseTreeNode.closestParentVerbNode()
#       if closestVerb != None and closestVerb.token != None:
# #        out.write(closestVerb.text+' ')
#         if closestVerb.token.lemma not in verbRuleCounts:
#           verbRuleCounts[closestVerb.token.lemma] = IRstats()  
#         if token.hasAnnotation(entityType):
#           verbRuleCounts[closestVerb.token.lemma].incTP()
# #          print '+TP (',closestVerb.token.lemma,'): ',token.text  
#         else:
#           verbRuleCounts[closestVerb.token.lemma].incFP()

#       for dep in token.governors:
#         if dep.isRoot() == False and dep.type == 'dobj':
#           depToken = token.sentence[dep.index]
#           if depToken.pos[0:2] == 'VB':
#             if depToken.lemma not in verbRuleCounts:
#               verbRuleCounts[depToken.lemma] = IRstats()  
#             if token.hasAnnotation(entityType):
#               verbRuleCounts[depToken.lemma].incTP()
#             else:
#               verbRuleCounts[depToken.lemma].incFP()

      for dep in token.governors:
        if dep.isRoot() == False and dep.type == 'pobj':
          depToken = token.sentence[dep.index]
#          print depToken.text, token.text
          for g in depToken.governors:
            if g.isRoot() == False:# and g.type == 'prep':
              gToken = token.sentence[g.index]
#              print gToken.text+'_'+g.type, depToken.text, token.text
              if gToken.pos[0:2] == 'VB':
                if gToken.lemma not in verbRuleCounts:
                  verbRuleCounts[gToken.lemma] = IRstats()  
                if token.hasAnnotation(entityType):
                  verbRuleCounts[gToken.lemma].incTP()
                else:
                  verbRuleCounts[gToken.lemma].incFP()
    
    for token in sentence:
    
      for type in entityTypes:
        if token.hasAnnotation(type):
          entityTokenCounts[type] += 1
        
    # for token in sentence 
#     for token in sentence:
#       if token.text != 'greater' and token.text != 'less':
#         continue
#       
#       nextToken = token.nextToken()
#       if nextToken == None or nextToken.text != 'than':
#         continue     
#       
#       prevToken = token.previousToken()
#       if prevToken == None or prevToken.text.lower() == 'p':
#         continue
#         
#       nextNextToken = nextToken.nextToken()
#       if nextNextToken == None or nextNextToken.isNumber() == False:
#         continue 
#       
#       patternOut.write(token.parseTreeNode.parent.treebankString()+'\n')
#       patternOut.write(token.text+' '+nextToken.text+' '+nextNextToken.text+'\n')
#             
#       # so far we have 'greater/less' 'than', check if parent phrase
#       # is a quantifier phrase
#       if token.parseTreeNode != None and token.parseTreeNode.parent != None \
#         and token.parseTreeNode.parent.parent != None:
#         patternOut.write(token.parseTreeNode.parent.parent.parent.treebankString()+'\n')
#         patternOut.write(token.parseTreeNode.parent.parent.parent.tokenString()+'\n')
#       patternOut.write('\n') 
       
    nTotalSentences += 1
    if sentence.hasNumbers():
      totalNumberSentenceCount += 1
    if sentence.section != None:
      if sentence.section in totalSectionCounts:
        totalSectionCounts[sentence.section] += 1
      else:
        totalSectionCounts[sentence.section] = 1
        
      if sentence.nlmCategory in totalNlmLabelCounts:
        totalNlmLabelCounts[sentence.nlmCategory] += 1
      else:
        totalNlmLabelCounts[sentence.nlmCategory] = 1

      if sentence.index in totalSentenceNumber:
        totalSentenceNumber[sentence.index] += 1
      else:
        totalSentenceNumber[sentence.index] = 1
              
    for token in sentence:
      if token.hasAnnotation(entityType):
        nSentences += 1
        if sentence.hasNumbers():
          numberSentenceCount += 1
        if sentence.section != None:
          if sentence.section in sectionCounts:
            sectionCounts[sentence.section] += 1
          else:
            sectionCounts[sentence.section] = 1
            
          if sentence.nlmCategory in nlmLabelCounts:
            nlmLabelCounts[sentence.nlmCategory] += 1
          else:
            nlmLabelCounts[sentence.nlmCategory] = 1

          if sentence.index in sentenceNumber:
            sentenceNumber[sentence.index] += 1
          else:
            sentenceNumber[sentence.index] = 1
        break

#     simpleTree = sentence.getSimpleTree()
#     for stTokenNode in simpleTree.tokenNodes():
#       if stTokenNode.isNounPhraseNode():
#         if stTokenNode.isEntityNP(entityType):
#           labeledPhrase = True
#         else:
#           labeledPhrase = False
#           
#         closestVerb = stTokenNode.closestParentVerbNode()
#         if closestVerb != None and closestVerb.token != None:
#   #        out.write(closestVerb.text+' ')
#           if closestVerb.token.lemma not in verbRuleCounts:
#             verbRuleCounts[closestVerb.token.lemma] = IRstats()  
#           if labeledPhrase:
#             verbRuleCounts[closestVerb.token.lemma].incTP()
# #            print '+TP (',closestVerb.token.lemma,'): ',stTokenNode.treeString(includeNP=True)  
#           else:
#             verbRuleCounts[closestVerb.token.lemma].incFP()
# #            print '-FP (',closestVerb.token.lemma,'): ',stTokenNode.treeString(includeNP=True)  
#         elif closestVerb != None and closestVerb.token == None:
#           print closestVerb.type, closestVerb.text
#                 
    for token in sentence:
      if token.hasAnnotation(entityType):
        # sentence contains desired entity, analyze it
        if entityType == 'outcome' \
          and token.getAnnotationAttribute('outcome', 'type') == 'good':
          entityOut.write('GOOD OUTCOME\n')
        # print parse tree
#        contextOut.write('\n'+sentence.getPrettyParseString()+'\n')
                  
        # build simplified parse tree with chunked NPs
        simpleTree = sentence.getSimpleTree()
#        contextOut.write('\n'+simpleTree.prettyTreebankString()+'\n')
        # print sentence with mentions substituted
#        writeSubstitutedSentence(entityOut, sentence, entityTypes)

#        entityOut.write(sentence.simpleTree.treeString()+'\n')
#        entityOut.write(sentence.simpleTree.treeString(includeNP=True, npEntityType=entityType)+'\n')
#        writeUMLSSentence(entityOut, sentence)

        writeSubstitutedSentence(entityOut, sentence, entityTypes)
        
        writeSubstitutedSentence(contextOut, sentence, entityTypes)
#        writeUMLSSentence(contextOut, sentence)
#        contextOut.write('\n'+simpleTree.treeString()+'\n')

#        contextOut.write('\n'+simpleTree.treeString(includeNP=True, npEntityType=entityType)+'\n')
        [ep, np] = simpleTree.countEntityNP(entityType)
        entityPhrases += ep
        nounPhrases += np
#        contextOut.write('entity phrases:' + str(ep) + ' noun phrases: ' + str(np) + '\n')

        sSentence = sentence.getSimplifiedSentence(entityTypes, 'train')
        s = sSentence.toString()
        contextOut.write(s+'\n\n')
#        entityOut.write(s+'\n')
        entityOut.write('\n')
        
        # look for key verbs
        mallet.findPathToVerb(sentence, entityType, pathCounts)
        findKeyVerbs(contextOut, sentence, entityType, verbCounts)
        break

contextOut.write('Entity token counts\n')
for eType in entityTokenCounts:
  contextOut.write(eType.upper()+': ' + str(entityTokenCounts[eType])+'\n')
  
        
# output verb frequency 
verbCounts = sorted(verbCounts.iteritems(), key=lambda (k, v): (v, k), \
                      reverse=True)

contextOut.write('\n\nParent verb frequency\n')
for v, c in verbRuleCounts.items():
  c.addFN(entityTokenCounts[entityType] - c.tp)
verbRuleCounts = sorted(verbRuleCounts.iteritems(), key=lambda (k, v): (v.smoothedPrecision(), k), \
                      reverse=True)
                      
for v, c in pathCounts.items():
  c.addFN(entityTokenCounts[entityType] - c.tp)
pathCounts = sorted(pathCounts.iteritems(), key=lambda (k, v): (v.smoothedPrecision(), k), \
                      reverse=True)

for v, c in verbCounts:
  contextOut.write(v+': '+str(c)+'\n')

contextOut.write('---\n')
for v, c in verbRuleCounts:
  if c.tp>10:
    contextOut.write('%s: %d/%d (p=%.2f,r=%.2f, f=%.2f)\n' \
         % (v.ljust(10), c.tp, c.tp+c.fp, c.smoothedPrecision(), c.smoothedRecall(), c.smoothedFscore()))

contextOut.write('\n\nDependency paths to verb\n')
for v, c in pathCounts:
  if c.tp>0:
    contextOut.write('%s: %d/%d (p=%.2f,r=%.2f, f=%.2f)\n' \
         % (v.ljust(10), c.tp, c.tp+c.fp, c.smoothedPrecision(), c.smoothedRecall(), c.smoothedFscore()))

dependencyPaths = mallet.importantDependencyPaths(absList, [entityType])
for path in dependencyPaths[entityType]:
  print path
  
contextOut.write('NP with all tokens labeled:' + str(entityPhrases) \
            + ' noun phrases with at least one token labeled: ' + str(nounPhrases) +' ')
contextOut.write(str(100*float(entityPhrases)/nounPhrases)+'%\n')  

primaryOutcomeOut.close()
patternOut.close()
entityOut.close()
contextOut.close()

print totalSentenceNumber
print sentenceNumber
print
print totalNlmLabelCounts
print nlmLabelCounts

for label,count in sectionCounts.items():
  print '%s: %d/%d (%.2f)'%(label, count, totalSectionCounts[label],\
       float(count)/totalSectionCounts[label])
print 
for label,count in nlmLabelCounts.items():
  print '%s: %d/%d (%.2f)'%(label, count, totalNlmLabelCounts[label],\
       float(count)/totalNlmLabelCounts[label])

print 
for label,count in sentenceNumber.items():
  print '%s: %d/%d (%.2f)'%(label, count, totalSentenceNumber[label],\
       float(count)/totalSentenceNumber[label])

print '%% of entity sentences containing numbers: %d/%d (%.2f)' \
    % (numberSentenceCount, totalNumberSentenceCount, \
       float(numberSentenceCount)/totalNumberSentenceCount)
