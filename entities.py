#!/usr/bin/python
# author: Rodney Summerscales

class Entities:
  """ Maintain lists of all types of unique entities in a study """
  lists = {}
  abstract = None
  featureVectors = []  # list of feature vectors for each mention pair
  prob = []          # 2D array with prob for mention pairs belonging in same entity
  
  def __init__(self, abstract):
    """ create a new collection of entity lists for a given abstract. 
        do not populate the list yet """
    self.abstract = abstract
    self.lists = {}
    self.featureVectors = []
    self.prob = []
    
  def createEntities(self, type, sentenceFilter, useDetected=True, useIds=False, mergeExactOnly=False):
    """ create an inital list of entities of a given type.
        "Identical" entities will be merged at this point.
        
        type = {'outcome', 'group', 'condition', ...}
        useDetected = True if should use mentions detected by system,
                  otherwise use annotated mentions
        useIds = True if merging process should use annotated ids
     """
    self.lists[type] = []
    if (type == 'group' or type == 'condition') and useIds == False and mergeExactOnly == False:
      # when merging entities from sentence with global list of entities,
      # merge the sentence entity with the best matching entity from the global list
      useBestMatch = True
    else:
      useBestMatch = False    
      
    for sentence in self.abstract.sentences: 
      # determine if we want to skip this sentence or not
      if sentenceFilter(sentence): 
        # are we clustering annotated or detected mentions? 
        if useDetected == True:
          templates = sentence.templates
        else:
          templates = sentence.annotatedTemplates
        
        # first cluster identical mentions within sentence
        sentenceEntities = []
        for mTemplate in templates.getList(type): 
          self.addToList(mTemplate, sentenceEntities, useIds, mergeExactOnly, appendUnmatched=True)
        
        # now merge this list with the entity list for the abstract
        if useBestMatch:
          unmatchedMentions = []
          for mTemplate in sentenceEntities:
            wasAppended = self.addToList(mTemplate, self.lists[type], useIds, mergeExactOnly, appendUnmatched=False)
            if wasAppended == False:
              unmatchedMentions.append(mTemplate)
          if len(unmatchedMentions) > 0:
            # try to find the most likely entity that this mention belongs to
#            print 'Unmatched:'
#            for m in unmatchedMentions:
#              print ' --',m.name
#            print 'Global entities:'
#            for m in self.lists[type]:
#              print ' --', m.name      
#            print '++ MERGING...'
            self.mergeUsingBestPossibleMatch(unmatchedMentions, self.lists[type])      
        else:
          for mTemplate in sentenceEntities:
            self.addToList(mTemplate, self.lists[type], useIds, mergeExactOnly, appendUnmatched=True)        

  def mergeUsingBestPossibleMatch(self, candidateList, destinationList):
    """ merge mentions from candidate list from those in destination list. 
        Mentions with non-trivial overlap are merged (assuming there is no ambiguity).
        Unmatched mentions are appended to the destination list """
    matches = {}    
    for mTemplate in candidateList:
      matches[mTemplate] = []
      for rootTemplate in destinationList:
        (nMatched, nUnmatched1, nUnmatched2) = mTemplate.partialSetMatch(rootTemplate)
        
        # if we are merging groups, do they have the same role (experiment, control)?
        sameRole = False
        if nMatched == 0 and mTemplate.type == 'group' \
          and ((mTemplate.isControl() and rootTemplate.isControl()) or (mTemplate.isExperiment() and rootTemplate.isExperiment())):
          sameRole = True
          
        if nMatched > 0 or sameRole:
          # there is a partial match
          matches[mTemplate].append(rootTemplate)

          if rootTemplate in matches:
            matches[rootTemplate].append(mTemplate)
          else:
            matches[rootTemplate] = [mTemplate]
          
    # if a candidate entity matched more than one global entity, do not merge
    # if multiple candidates match the same global entity, do not merge
    for mTemplate in candidateList:
      matchingTemplate = None
      if len(matches[mTemplate]) == 1:
        # candidate entity matches only ONE global entity
        rootTemplate = matches[mTemplate][0]
        if len(matches[rootTemplate]) == 1:
          # global entity has only ONE match
          matchingTemplate = rootTemplate
#      elif len(matches[mTemplate]) > 1:
#        print mTemplate.name, 'has multiple matches'
#        for m in matches[mTemplate]:
#          print '    ** matches:', m.name
      if matchingTemplate != None:
        self.mergeTemplates(rootTemplate, mTemplate, destinationList)  
      else:
        # no match found, just append list of global entities
        self.appendEntity(mTemplate, destinationList)    
#        print '!!! Merging unsuccessful:', mTemplate.name    
        
                               
          
  def addToList(self, mTemplate, templateList, useIds, mergeExactOnly, appendUnmatched):
    """ add mention template to given list of templates. If possible, merge with matching mention cluster. 
        Return True if mention added to list, False otherwise. """
    foundMatch = False
    for rootTemplate in templateList:
      if self.matchesRootTemplate(mTemplate, rootTemplate, useIds, mergeExactOnly):
        foundMatch = True
        self.mergeTemplates(rootTemplate, mTemplate, templateList)           
#            rootTemplate.merge(mTemplate)
        return True
      
    if foundMatch == False and appendUnmatched == True:
      # entity is unique so far, add it to the list
      self.appendEntity(mTemplate, templateList)
      return True
    else:
      return False   # mention was not added to list

  def isAppositiveMention(self, mTemplate1, mTemplate2):
    """ return True if one of the mentions is an appositive of the other """
    for token in mTemplate1.mention.tokens:
      for dep in token.dependents:
        if dep.type == 'appos':
          depToken = token.sentence[dep.index]
          if mTemplate2.mention.containsToken(depToken):
            return True
      for gov in token.governors:
        if gov.type == 'appos':
          govToken = token.sentence[gov.index]
          if mTemplate2.mention.containsToken(govToken):
            return True
    return False
          
  def matchesRootTemplate(self, candidateTemplate, rootTemplate, useIds, mergeExactOnly):
    """ return True if a candidate template matches the root template of an existing cluster """
    foundMatch = False
    if useIds and self.idMatch(rootTemplate, candidateTemplate):
      # using annotated IDs and both templates have matching IDs
      foundMatch = True
    elif useIds == False:
      if mergeExactOnly:
        # only merge mentions that are identical
        if candidateTemplate.matchesTemplateExact(rootTemplate):
          foundMatch = True
      else:
        for mTemplate in rootTemplate.getMentionChain():
          if (mTemplate.exactSetMatch(candidateTemplate) \
              or (mTemplate.type == 'group' and self.isAppositiveMention(mTemplate, candidateTemplate)) \
              or (mTemplate.type == 'outcome' and self.outcomesCorefer(mTemplate, candidateTemplate))):
            # not using annotated IDs
            # the two must be exact matches
            foundMatch = True
            break
      
    return foundMatch


  def outcomesCorefer(self, t1, t2):
    """ return true if two outcomes corefer. Specifically if one outcome is a 
       referring expression (e.g. primary outcome) and the other is not. """ 
    if len(t1.primaryOutcomeId) > 0 and len(t2.primaryOutcomeId) > 0 \
         and t1.primaryOutcomeId == t2.primaryOutcomeId:
      return True
    else:          
      return False
      
  def createTrueEntities(self, type, sentenceFilter):
    """ create list of entities of a given type using all annotated information
    """
#    print 'Creating true templates:',
    self.createEntities(type, sentenceFilter, useDetected=False, useIds=True)
#    print type, len(self.getList(type))
    
  def getList(self, type):
    """ return list of templates of a given template type """
    return self.lists.get(type, [])


  def idMatch(self, m1, m2):
    """ return True if the two mentions have matching annotated ids """
    if len(m1.getAnnotatedId()) > 0 and m1.getAnnotatedId() == m2.getAnnotatedId():
      return True
    if len(m1.getAnnotatedId()) == 0 or len(m2.getAnnotatedId()) == 0:
      if m1.exactSetMatch(m2):
        return True
    return False


  def mergeTemplates(self, mTemplate1, mTemplate2, entityList):  
    """ merge two templates. merge the shorter one into the longer one.
        if the merged template is not already in the given list, add it """           
    rootMention1 = mTemplate1.rootMention()
    rootMention2 = mTemplate2.rootMention()
    # link the two mentions
    nTokens1 = len(rootMention1.mention.tokens)
    nTokens2 = len(rootMention2.mention.tokens)
    if nTokens1 > nTokens2 and nTokens1 < 8:
      newChild = rootMention2
      parentMention = rootMention1
    else:
      newChild = rootMention1
      parentMention = rootMention2
      
    if self.isMentionInList(newChild, entityList): 
      self.removeEntity(newChild, entityList)  
      
    parentMention.merge(newChild)
    
    if self.isMentionInList(parentMention, entityList) == False:
      self.appendEntity(parentMention, entityList)

  def appendEntity(self, mTemplate, entityList):
    """ add mention template to current list of mentions """
    if self.isMentionInList(mTemplate, entityList) == False:
      entityList.append(mTemplate.rootMention()) 
      
  def removeEntity(self, mTemplate, entityList):
    """ remove the entity containing a given mention from list of entities
       mTemplate = mention template for given mention
       """
    rMention = mTemplate.rootMention()
    if self.isMentionInList(rMention, entityList):
      entityList.remove(rMention)
    else:
      print 'Error: Trying to remove a mention from the list when it is not there'
      print rMention.name, rMention, entityList
 
  def isMentionInList(self, mTemplate, entityList):
    """ return true if this mention is in the current list of entities """
    rMention = mTemplate.rootMention()
    return rMention in entityList
#    return rMention in self.lists[mTemplate.type] 



