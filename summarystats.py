#!/usr/bin/python
# author: Rodney Summerscales
# class definitions for summary statistic templates

import math
import sys
import heapq
import cStringIO

from outcomemeasurementtemplates import OutcomeMeasurement
from basetemplate import Evaluation

# store all of the summary stat templates for an abstract
class SummaryStats:
  groupSizes = []         # group size templates for an abstract
  outcomeNumbers = []     # outcome number templates for an abstract
  eventRates = []         # event rate templates for an abstract
  unmatchedMeasurements = []  # list of unmatched outcome measurements
  stats = []       # summary stat templates
  trueStats = False       # templates contain ground truth summary stats
  groupsById = {}
  outcomesById = {}
  timesById = {}
  abstract = None
  incompleteOutcomeMeasurements = []
  discardedMeasurements = []
  irStats = None
  
  def __init__(self):
    self.groupSizes = []
    self.outcomeNumbers = []
    self.eventRates = []
    self.unmatchedMeasurements = []
    self.discardedMeasurements = []
    self.incompleteOutcomeMeasurements = []
    self.stats = []
    self.trueStats = False
    self.groupsById = {}
    self.outcomesById = {}
    self.timesById = {}
    self.abstract = None


  def numberOfDetectedStats(self):
    """ return the number of ARR values computed from detected info """
    return len(self.stats)
  
  def numberOfTrueStats(self):
    """ return the number of ARR values computed from *annotated* info """
    return len(self.trueStats)

  def computeDetectedStats(self, abstract):
    """ identify outcome measurements for same outcome (different groups) and compute absolute risk reduction """
    self.groupSizes = []
    self.outcomeNumbers = []
    self.eventRates = []
    self.stats = []
    self.trueStats = False
    self.abstract = abstract

    # pair outcome measurements for same outcome in same sentence, for different groups
    omHash = {}
    for oTemplate in abstract.entities.getList('outcome'):
      oTemplate.unusedNumbers = []
      omList = oTemplate.getOutcomeMeasurements()
      if len(omList) > 1:
        # there are at least *two* measurements for this outcome
        omHash[oTemplate] = {}
        for om in omList:
          if om.eventRate() != None:
            sentence = om.getSentence()
            if sentence not in omHash[oTemplate]:
              omHash[oTemplate][sentence] = {}
              
            group = om.getGroup()
            if group not in omHash[oTemplate][sentence]:
              omHash[oTemplate][sentence][group] = []
            
            omHash[oTemplate][sentence][group].append(om)   
                      
    # now try to pair up outcome measurements for the same outcome in same sentence
    for oTemplate in omHash.keys():
      for s in omHash[oTemplate].keys():
        groupList = omHash[oTemplate][s].keys()
        # check for multiple measurements for same group,outcome
        # for now, delete them
        for gTemplate in groupList:
          if len(omHash[oTemplate][s][gTemplate]) != 1:
            print abstract.id, '!!! Illegal number of outcome measurements:', len(omHash[oTemplate][s][gTemplate])
            print 'Outcome =', oTemplate.name
            print 'Group =', gTemplate.name       
            for om in omHash[oTemplate][s][gTemplate]:
              om.display()
            omHash[oTemplate][s][gTemplate] = []
            
        for i in range(0, len(groupList)-1):
          gTemplate = groupList[i]
          if len(omHash[oTemplate][s][gTemplate]) > 0:
            # skip measurements for this group for now if there is more than one measurement for this group,outcome
            # NOTE: with current matching scheme, it should not be possible for a group to have more than *one*
            #       measurement for an outcome. Others should have been discarded.
            #       *However*, it is possible when using annotated info for associations (for ceiling analysis)
            om1 = omHash[oTemplate][s][gTemplate][0]
            for j in range(i+1, len(groupList)):
              gTemplate2 = groupList[j]
              if len(omHash[oTemplate][s][gTemplate2]) == 1:
                om2 = omHash[oTemplate][s][gTemplate2][0]
                ssTemplate = SummaryStat(om1, om2)
                self.stats.append(ssTemplate)
                om1.used = True
                om2.used = True             
        
        # check for unused outcome measurements                
        for gTemplate in groupList:
          if len(omHash[oTemplate][s][gTemplate]) == 1:
            om = omHash[oTemplate][s][gTemplate][0]
            if om.used == False:
              # we could not find a matching measurement, add to list of unused
              oTemplate.unusedNumbers.append(om)
    


  def detectedMatch(self, omTemplate1, omTemplate2):
    """ check if two outcome measurement templates should be paired in 
        a summary statistic """
    return omTemplate1.isComplete() and omTemplate2.isComplete() \
          and omTemplate1.getTime() == omTemplate2.getTime()  \
          and omTemplate1.getGroup().exactSetMatch(omTemplate2.getGroup()) == False
    
    
                 
  def computeTrueStats(self, abstract):
    """ compute summaries statistics using annotations """
    self.outcomeNumbers = []
    self.eventRates = []
    self.stats = []
    self.trueStats = True
    self.abstract = abstract
    
    self.groupsById = {}
    self.outcomesById = {}
    self.timesById = {}
 
    omHash = {}
    
    for s in abstract.sentences:
      # find all of the annotated templates in the sentence
      templates = s.annotatedTemplates
      gList = templates.getList('group')
      oList = templates.getList('outcome')
      gsList = templates.getList('gs')
      onList = templates.getList('on') 
      erList = templates.getList('eventrate')     
      tList = templates.getList('time')
      
#      print abstract.id
#      for er in erList:
#        print er.value,
#      print
      
      for t in tList:
#         times.append(t)
        if t.getAnnotatedId() in self.timesById:
          self.timesById[t.getAnnotatedId()].merge(t)
        else:
          self.timesById[t.getAnnotatedId()] = t
          
      for g in gList:
#         groups.append(g)
        if g.getAnnotatedId() in self.groupsById:
          self.groupsById[g.getAnnotatedId()].merge(g)
        else:
          self.groupsById[g.getAnnotatedId()] = g

      for outcome in oList:
#         outcomes.append(outcome)
        if outcome.getAnnotatedId() != None and len(outcome.getAnnotatedId()) > 0:
          if outcome.getAnnotatedId() in self.outcomesById:
            self.outcomesById[outcome.getAnnotatedId()].merge(outcome)
          else:
            self.outcomesById[outcome.getAnnotatedId()] = outcome
        else:
          print abstract.id, outcome.name, 'does not have an ID.',
          print 'Not using it for summary stats.'

#       for gs in gsList:
#         self.groupSizes.append(gs)

      # link groups and their sizes
      for gs in gsList:
        gid = gs.token.getAnnotationAttribute('gs', 'group')
        if gid in self.groupsById:
          g = self.groupsById[gid]
          gs.group = g
          g.addSize(gs)
        tid = gs.token.getAnnotationAttribute('gs', 'time')
        if tid in self.timesById:
          t = self.timesById[tid]
          gs.time = t
          
#       for gid,g in self.groupsById.items():
#         print 'Group id:', gid, ', name = ', g.name, ', size =', g.getSize()
         
      # link all relevant information needed for each outcome measurement
      for on in onList:
        gid = on.token.getAnnotationAttribute('on', 'group')
        oid = on.token.getAnnotationAttribute('on', 'outcome')
        tid = on.token.getAnnotationAttribute('on', 'time')
        csID = on.token.getAnnotationAttribute('on', 'compareSet')
#        print 'on:',on.value, csID
        
        if oid in self.outcomesById:
          oTemplate = self.outcomesById[oid]
          gTemplate = self.groupsById.get(gid, None)        
          tTemplate = self.timesById.get(tid, None)
          
          if oid not in omHash:
            omHash[oid] = []
            
          om = OutcomeMeasurement(on)              
          om.addGroup(gTemplate)
          om.addOutcome(oTemplate)
          om.addTime(tTemplate)
          omHash[oid].append(om)
        else:
          print abstract.id, '??? Outcome number', on.value, 
          print 'does not have a matching outcome with id =', oid
#         print '-->',
#         om.write(sys.stdout)
        
        

             
      for er in erList:
        gid = er.token.getAnnotationAttribute('eventrate', 'group')
        oid = er.token.getAnnotationAttribute('eventrate', 'outcome')
        tid = er.token.getAnnotationAttribute('eventrate', 'time')
        csID = er.token.getAnnotationAttribute('eventrate', 'compareSet')
#        print abstract.id+': er: ',er.value, csID
        
        if oid in self.outcomesById:
          oTemplate = self.outcomesById[oid]
          gTemplate = self.groupsById.get(gid, None)        
          tTemplate = self.timesById.get(tid, None)
          
#          print abstract.id+': er: ', er.value, gTemplate, tTemplate, csID
          
          if oid not in omHash:
            omHash[oid] = []
          matchFound = False            
          for om in omHash[oid]:
            if om.getGroup() == gTemplate and om.getTime() == tTemplate and om.getCompareSetID() == csID:
              om.addEventRate(er)
#              print 'adding', er.value
#              om.write(sys.stdout)
              matchFound = True
              break
#            else:
#              print om.getGroup(), om.getTime(), om.getCompareSetID
              
          if matchFound == False:
            # event rate not added to existing outcome measurement, create new measurement
            om = OutcomeMeasurement(er)
            om.addGroup(gTemplate)
            om.addOutcome(oTemplate)
            om.addTime(tTemplate)
            omHash[oid].append(om)
        else:
          print 'Event rate missing outcome annotation in abstract ',
          print abstract.id, ':', s.toString()
          er.write(sys.stdout)     
     
        
    for oid in omHash.keys():
      omList = omHash[oid]
      for i in range(0, len(omList)):
        om1 = omList[i]
        csID1 = om1.getCompareSetID()
#        print abstract.id, csID1,':',
        for j in range(i+1, len(omList)):
          om2 = omList[j]
          csID2 = om2.getCompareSetID()
#          print csID2,
          if csID1 == csID2 and om1.isComplete() and om2.isComplete() \
            and om1.getGroup() != om2.getGroup() and om1.getTime() == om2.getTime():
            ssTemplate = SummaryStat(om1, om2, useAnnotated=True)
            self.stats.append(ssTemplate)
            om1.used = True
            om2.used = True
#        print
        if om1.used == False:
          self.unmatchedMeasurements.append(om1)
            
    for om in self.unmatchedMeasurements:
      if om.getOutcome() != None:
        om.getOutcome().unusedNumbers.append(om)   


  def matchAnnotatedEventRates(self, annotatedStats):
    """ try to match unused detected event rates with annotated event rates 
        in the unused annotated outcome measurements and unmatched annotated summary stats 
        """
    matchSets = {}    
    outcomeList = self.abstract.entities.getList('outcome')
    for oTemplate in outcomeList:
      for om in oTemplate.unusedNumbers:
        matchSets[om] = []

        # check unused annotated numbers for matches
        for annotatedOutcome in self.abstract.annotatedEntities.getList('outcome'):
          for annotatedOM in annotatedOutcome.unusedNumbers:
            if om.matchAnnotatedMentions(annotatedOM):
              annotatedER = annotatedOM.eventRate()
              if annotatedER != None:
                dist = abs(om.eventRate() - annotatedER)
                heapq.heappush(matchSets[om], (dist, annotatedOM))
                if annotatedOM not in matchSets:
                  matchSets[annotatedOM] = []
                heapq.heappush(matchSets[annotatedOM], (dist, om))
        # check unmatched annotated ARR stats for matches
        for aSS in annotatedStats.stats:
          if aSS.matchingStat == None:
            if om.matchAnnotatedMentions(aSS.lessEffective):
              annotatedOM = aSS.lessEffective
            elif om.matchAnnotatedMentions(aSS.moreEffective):
              annotatedOM = aSS.moreEffective
            else:
              annotatedOM = None
            if annotatedOM != None:
              dist = abs(om.eventRate() - annotatedOM.eventRate())
              heapq.heappush(matchSets[om], (dist, annotatedOM))
              if annotatedOM not in matchSets:
                matchSets[annotatedOM] = []
              heapq.heappush(matchSets[annotatedOM], (dist, om))
                      
    for oTemplate in outcomeList:
      for om in oTemplate.unusedNumbers:
        if len(matchSets[om]) > 0:
          annotatedOM = matchSets[om][0][1]
          if matchSets[annotatedOM][0][1] == om:
            # the annotated and detected stats are the best matches for each other
            om.matchingOM = annotatedOM
            annotatedOM.matchingOM = om
            if matchSets[annotatedOM][0][0] < 0.001:
              om.correctlyMatched = True
              annotatedOM.correctlyMatched = True
            
             
  def matchAnnotatedStats(self, annotatedStats):
    """ try to find annotated summary stat templates that match the detected ones """
    if len(annotatedStats.stats) == 0 or len(self.stats) == 0 or self.abstract == None:
      return   # nothing to match with
      
    matchSets = {}
    outcomeList = self.abstract.entities.getList('outcome')
    for oTemplate in outcomeList:
      if len(oTemplate.summaryStats) > 0:
        for dSS in oTemplate.summaryStats:          
          for aSS in annotatedStats.stats:
            if aSS.correctlyMatched == False and dSS.outcome.matchAnnotated(aSS.outcome):
              # same outcome, check groups
              if dSS.groupsMatch(aSS):
                # outcome and groups match, add these to list for this outcome
                # check them later
                dist = dSS.arrError(aSS)
                
                if dSS not in matchSets:
                  matchSets[dSS] = []
                if aSS not in matchSets:
                  matchSets[aSS] = []
                  
                heapq.heappush(matchSets[dSS], (dist, aSS))
                heapq.heappush(matchSets[aSS], (dist, dSS))
#              else:
#                print self.abstract.id, 'Groups do not match'
#                print 'Less effective:', dSS.lessEffective.getGroup().matchAnnotated(aSS.lessEffective.getGroup()),
#                print dSS.lessEffective.getGroup().name, 
#                print dSS.lessEffective.getGroup().mention.matchedMention,
#                print dSS.lessEffective.getGroup().rootMention().mention.matchedMention
#                print 'More effective:', dSS.moreEffective.getGroup().matchAnnotated(aSS.moreEffective.getGroup()),
#                print dSS.moreEffective.getGroup().name, 
#                print dSS.moreEffective.getGroup().rootMention().mention.matchedMention
#                print 'annotated:'
#                print aSS.lessEffective.getGroup().name,
#                print aSS.lessEffective.getGroup().mention.text,
#                print aSS.lessEffective.getGroup().mention
#                aSS.lessEffective.getGroup().display()
#                print aSS.moreEffective.getGroup().name,
#                print aSS.moreEffective.getGroup().mention.text,
#                print aSS.moreEffective.getGroup().mention
#                aSS.moreEffective.getGroup().display()
                 
    # prune away sub optimal matches
    # convert min heap into list of min matches
    for ss in matchSets:
      if len(matchSets[ss]) > 1:
        (minDist, matchedSS) = heapq.heappop(matchSets[ss])
        newMatchedSet = [(minDist, matchedSS)]
        for (dist, matchedSS) in matchSets[ss]:
          if dist <= minDist:
            newMatchedSet.append((dist, matchedSS))
        matchSets[ss] = newMatchedSet
        for dist, mSS in matchSets[ss]:
          print dist,
        print
                      
    for oTemplate in outcomeList:
      for dSS in oTemplate.summaryStats:
        if dSS.correctlyMatched == False and dSS in matchSets and len(matchSets[dSS]) > 0:
          for (dist, aSS) in matchSets[dSS]:            
            if aSS.matchingStat == None:
              # check if the detected ARR is an optimal match for the true one
              bestMatch = False
              for (dist, ss) in matchSets[aSS]:
                if dSS == ss:
                  bestMatch = True
                  break
              if bestMatch:
                # the annotated and detected stats are the best matches for each other
                dSS.matchingStat = aSS
                aSS.matchingStat = dSS
                arr = dSS.arr
                if (dist < 0.001 and dSS.sameSign(aSS)) or (dist == 0 and arr == 0):
                  dSS.correctlyMatched = True
                  aSS.correctlyMatched = True
                break
                  
  # output summary stats to a file
  def writeSummaryStats(self, out):
    for ssTemplate in self.stats:
      ssTemplate.write(out)
      if ssTemplate.matchingStat != None:
        sameSign = ssTemplate.sameSign(ssTemplate.matchingStat)
        err = ssTemplate.arrError(ssTemplate.matchingStat)
        out.write('===== Matches (CORRECT = %s, ERROR = %.4f, SAME_SIGN = %s, EVAL = %s) =====\n' \
                  % (ssTemplate.correctlyMatched, err, sameSign, ssTemplate.evaluation.getRating()))        
        ssTemplate.matchingStat.write(out)
      out.write('\n')
 
  def writeUnusedNumbers(self, out):
    outcomeList = self.abstract.entities.getList('outcome')
    for oTemplate in outcomeList:
      for om in oTemplate.unusedNumbers:
        om.write(out)
        if om.matchingOM != None:
          err = abs(om.eventRate() - om.matchingOM.eventRate())
          if om.correctlyMatched == True:
            out.write('===== UNUSED Matches (CORRECT, ERROR = %.4f) =====\n'%err)        
          else:
            err = abs(om.eventRate() - om.matchingOM.eventRate())
            out.write('===== UNUSED Matches (ERROR = %.4f)=====\n'%err)
          om.matchingOM.write(out)
        else:
          out.write('*** UNMATCHED ***')  
        out.write('\n')
    
#############################################
# class definition for a summary set template
#############################################

class SummaryStat:
  arr = 0             # absolute risk reduction
  nnt = 0             # number needed to treat
  arrCI = []          # 95% confidence interval for ARR
  nntCI = []          # 95% confidence interval for NNT
  riskIncrease = False # moreEffective worse than lessEffective
  outcome = None
  moreEffective = None   # link to outcome measurement for experimental group
  lessEffective = None      # link to outcome measurement for lessEffective group
  roleConflict = True # is it unclear which is lessEffective, which is exp
  matched = False     # has this been matched to annotated/detect ss template?
  correctlyMatched = False  # the matched annotated/detected ss is correct
  duplicate = False   # there is another summary stat that is identical 
                      # except for some of the numbers (not counting time)
  time = None         # follow-up time when outcome was recorded
  matchingStat = None # the detected or annotated summary stat template matching this one
  useAnnotated = False # use annotated information instead of that determined by system
  evaluation = None
  
  def __init__(self, om1, om2, useAnnotated=False):
    self.matched = False
    self.duplicate = False
    self.matchingStat = None
    self.correctlyMatched = False
    self.evaluation = Evaluation()
    self.useAnnotated = useAnnotated
    self.outcome = om1.getOutcome()
    om1.getOutcome().summaryStats.append(self)
    if om2.getOutcome() != om1.getOutcome():
      om2.getOutcome().summaryStats.append(self)
      
#    if om1.getGroup().isControl() or om2.getGroup().isExperiment():
#      self.lessEffective = om1
#      self.moreEffective = om2
#      self.roleConflict = False
#      om1.getGroup().role = 'lessEffective'
#      om2.getGroup().role = 'moreEffective'
#    elif om1.getGroup().isExperiment() or om2.getGroup().isControl():
#      self.lessEffective = om2
#      self.moreEffective = om1
#      self.roleConflict = False
#      om2.getGroup().role = 'lessEffective'
#      om1.getGroup().role = 'moreEffective'
#    else: # not sure. say that the one with the better event rate is moreEffective
#      self.roleConflict = True
#      if om1.eventRate() > om2.eventRate():
#        self.lessEffective = om1
#        self.moreEffective = om2
#      else:
#        self.lessEffective = om2
#        self.moreEffective = om1
    er1 = om1.eventRate()
    er2 = om2.eventRate()
    if (self.outcome.outcomeIsBad(useAnnotatedPolarity=useAnnotated) == True and er1 > er2) \
       or (self.outcome.outcomeIsBad(useAnnotatedPolarity=useAnnotated) == False and er1 < er2):
      self.lessEffective = om1
      self.moreEffective = om2
    else:
      self.lessEffective = om2
      self.moreEffective = om1
        
    if om1.getTime() != None:
      self.time = om1.getTime()
    elif om2.getTime() != None:
      self.time = om2.getTime()
          
    worseER = self.lessEffective.eventRate()
    betterER = self.moreEffective.eventRate()
    if worseER == None or betterER == None:
      print self.lessEffective.getAbstract().id, 'ERROR: Outcome measurement does not have an event rate'
      self.lessEffective.display()
      self.moreEffective.display()
      
    self.arr = abs(worseER - betterER)
    
    leGS = self.lessEffective.getGroupSize()
    meGS = self.moreEffective.getGroupSize()
    noConfidenceIntervals = False
    if leGS == 0 or meGS == 0:
      noConfidenceIntervals = True
      error = 0
    elif worseER > 1 or betterER > 1:
      self.lessEffective.write(sys.stdout)
      self.moreEffective.write(sys.stdout)
      noConfidenceIntervals = True
      error = 0
    else:  
      x = betterER*(1-betterER)/meGS + worseER*(1-worseER)/leGS
      if worseER < 0 or worseER > 1 or betterER > 1 or betterER < 0 or leGS < 1 or meGS < 1:
        print self.outcome.mention.tokens[0].sentence.abstract.id,
        print ': Abstract contains negative outcome number, event rate or zero group size'
        print 'WorseER =', worseER, 'BetterER =', betterER, 'worseGS =', leGS, 'betterGS =',meGS
        print self.outcome.name
        print self.lessEffective.isComplete(), self.moreEffective.isComplete()
        sys.exit()
      error = 1.96*math.sqrt(x)
    
    if self.arr < 0:
      # we actually have a risk increase
      self.riskIncrease = True
      self.arr = -self.arr
    elif self.arr > 0:
      self.riskIncrease = False
     
    # if outcome is good, then flip polarity of risk reduction term  
#     if self.arr != 0 and self.outcome.outcomeIsBad(self.useAnnotated) == False:
#       if self.riskIncrease:
#         self.riskIncrease = False
#       else:
#         self.riskIncrease = True


    self.nnt = self.safeInverse(self.arr)
      
    if noConfidenceIntervals or self.infiniteNumberNeeded():
      self.arrCI = []
      self.nntCI = []
    else:
      self.arrCI = [self.arr - error, self.arr + error]
      self.nntCI = [self.safeInverse(self.arrCI[1]), \
                    self.safeInverse(self.arrCI[0])]
  
  def groupsMatch(self, annotatedStat):
    """ return True if the lessEffective and moreEffective group templates in the given annotated 
      summary stat template that matches the lessEffective and moreEffective templates
      for this summary stat template.
      
      otherwise return False """         
    # find matching groups
    if (self.lessEffective.getGroup().matchAnnotated(annotatedStat.lessEffective.getGroup())\
        and self.moreEffective.getGroup().matchAnnotated(annotatedStat.moreEffective.getGroup())) \
       or (self.lessEffective.getGroup().matchAnnotated(annotatedStat.moreEffective.getGroup())\
           and self.moreEffective.getGroup().matchAnnotated(annotatedStat.lessEffective.getGroup())):
      return True
    else:  
      return False

  def sameSign(self, annotatedStat):
    """ return True if this stat has the same sign as the given stat """
    if self.lessEffective.getGroup().matchAnnotated(annotatedStat.lessEffective.getGroup())\
      and self.moreEffective.getGroup().matchAnnotated(annotatedStat.moreEffective.getGroup()):
      # group roles the same for groups in annotated and detected
      return True
    
    if  self.lessEffective.getGroup().matchAnnotated(annotatedStat.moreEffective.getGroup())\
      and self.moreEffective.getGroup().matchAnnotated(annotatedStat.lessEffective.getGroup()) \
      and abs(self.arr) < 0.0001 and abs(annotatedStat.arr) < 0.0001:
      return True
    
    return False
    
  def arrError(self, annotatedStat):
    """ return the calculated error between this detected stat and the given annotated one 
        for now the error is  abs(C_D - C_A) + abs(E_D - E_A)
        where C_D, E_D are the DETECTED event rates for the lessEffective and moreEffective groups
          C_A, E_A are the ANNOTATED event rates for the lessEffective and moreEffective groups

        The error will range from 0 to 2 (worst case)
            """ 
    if self.lessEffective.getGroup().matchAnnotated(annotatedStat.lessEffective.getGroup())\
      and self.moreEffective.getGroup().matchAnnotated(annotatedStat.moreEffective.getGroup()):
      annotatedLessEffective = annotatedStat.lessEffective
      annotatedMoreEffective = annotatedStat.moreEffective     
    elif self.lessEffective.getGroup().matchAnnotated(annotatedStat.moreEffective.getGroup())\
      and self.moreEffective.getGroup().matchAnnotated(annotatedStat.lessEffective.getGroup()):
      annotatedLessEffective = annotatedStat.moreEffective
      annotatedMoreEffective = annotatedStat.lessEffective           
    else:
      return 2    

    leErrorComputed = abs(self.lessEffective.eventRate() - annotatedLessEffective.eventRate())
    leErrorText = abs(self.lessEffective.eventRate() - annotatedLessEffective.eventRate(useTextFirst=True))
    leError = min(leErrorComputed, leErrorText)

    meErrorComputed = abs(self.moreEffective.eventRate() - annotatedMoreEffective.eventRate())
    meErrorText = abs(self.moreEffective.eventRate() - annotatedMoreEffective.eventRate(useTextFirst=True))
    meError = min(meErrorComputed, meErrorText)

#    self.write(sys.stdout)
#    print meErrorComputed, meErrorText, meError, annotatedStat.moreEffective.hasEventRateValue()
#    print leErrorComputed, leErrorText, leError
#    print leError+meError
    
    return leError + meError
  
#    return abs(self.lessEffective.eventRate() - annotatedStat.lessEffective.eventRate()) \
#            + abs(self.moreEffective.eventRate() - annotatedStat.moreEffective.eventRate())
               
        
#  def exactStatMatch(self, annotatedStat):
#    """ return True if this detected stat is a perfect match for the numbers in a 
#        given annotated stat. 
#        Note that this only checks outcome numbers, group sizes and event rates.
#        It does not check if the outcomes are the same.
#        """
#    annotatedGroups = self.matchingControlExperimentGroups(annotatedStat)
#    if len(annotatedGroups) == 2:            
#      dC = self.lessEffective
#      dE = self.moreEffective
#      aC = annotatedGroups[0]
#      aE = annotatedGroups[1]
#      
#      # both groups match, so far so good
#      # now check for matching values
#      if (aC.getGroupSize() == dC.getGroupSize() \
#         and aE.getGroupSize() == dE.getGroupSize()\
#         and aC.getOutcomes() == dC.getOutcomes()\
#         and aE.getOutcomes() == dE.getOutcomes()) \
#         or (abs(aC.eventRate() - dC.eventRate()) < 0.001 \
#             and abs(aE.eventRate() - dE.eventRate()) < 0.001\
#             and abs(annotatedStat.arr - self.arr) < 0.01): 
#        return True
#          
#    return False

  def safeInverse(self, value):
    """ return the inverse of a given value or float('inf') if it is 
        very close to zero """
    if value < 1e-20 and value > -1e-20:
      return float('inf')
    else:      
      return (1.0/value)
    
  def arrString(self):
    """ return a formatted string containing the ARR/ARI """
    return '%.1f%%' % (self.arr*100)
    
  def nntString(self):
    """ return a formatted string containing the NNT/NNH """    
    return '%.1f' % self.nnt
    
  def hasConfidenceIntervals(self):
    return len(self.arrCI) > 0
    
  def infiniteNumberNeeded(self):
    return self.nnt == float('inf')
    
  def arrLowerBound(self):
    if self.hasConfidenceIntervals():
      return '%.1f%%' % (self.arrCI[0]*100)
    else: 
      return ''

  def arrUpperBound(self):
    if self.hasConfidenceIntervals():
      return '%.1f%%' % (self.arrCI[1]*100)
    else:    
      return ''
    
  def nntLowerBound(self):
    if self.hasConfidenceIntervals():
      return '%.1f, ' % self.nntCI[0]
    else:
      return ''
    
  def nntUpperBound(self):
    if self.hasConfidenceIntervals():
      if self.nntCI[1] < 0:
        return 'infinity'
      else:
        return '%.1f' % self.nntCI[1]
    else:  
      return ''
  
  def riskType(self):
    """ return the type of absolute risk statistic ('ARR' or 'ARI'). """
    if self.riskIncrease == True:
      return 'ARI'
    else:
      return 'ARR'
    
  def numberNeededType(self):
    """ return the type of number needed statistic ('NNT' or 'NNH'). """
    if self.riskIncrease == True:
      return 'NNH'
    else:
      return 'NNT'
    
  def display(self):  
    self.write(sys.stdout)
    
  def write(self, out):
    out.write('Outcome: '+self.outcome.name+'\n')
    if self.matchingStat == None:
      out.write('  *** UNMATCHED ***  \n')
#    if self.roleConflict == True:
#      out.write('  *** Group roles uncertain ***\n')
    if self.outcome.outcomeIsBad(useAnnotatedPolarity=True) == False:
      out.write('  *** Good outcome ***\n')
    if self.outcome.outcomeIsBad() == False:
      out.write('  *** OUTCOME PREDICTED GOOD ***\n')   
    tTemplate = self.moreEffective.getTime() 
    if tTemplate != None:
      out.write('  -- Follow-up time: %s\n' % tTemplate.toString())  
    out.write('  -- More effective: '+self.moreEffective.getGroup().name+':  ')
    out.write(self.moreEffective.statisticString()+'\n')
    out.write('  -- Less effective: '+self.lessEffective.getGroup().name+':  ')
    out.write(self.lessEffective.statisticString()+'\n')
        
    rLabel = self.riskType()
    nnLabel = self.numberNeededType()

    out.write('  -- '+rLabel+ ': ' + self.arrString())
    if self.hasConfidenceIntervals():
      out.write(',  95% confidence interval ['+self.arrLowerBound())
      out.write(',' + self.arrUpperBound() + ']')
            
    if self.infiniteNumberNeeded() == False:
      out.write('\n  -- '+nnLabel+ ': ' + self.nntString())
      if self.hasConfidenceIntervals():  
        out.write(',  95% confidence interval ['+ self.nntLowerBound())
        out.write(self.nntUpperBound()+']')
    out.write('\n')
    
  def toString(self):
    """ return string describing this entity """
    sio = cStringIO.StringIO()
    self.write(sio)
    s = sio.getvalue()
    sio.close()
    return s



