#!/usr/bin/python
# author: Rodney Summerscales
# base template for associating mentions with quantities

from finder import Finder
from finder import EntityStats
from statlist import StatList

###############################################################################
# class definition to store a feature vector for mention quantity association
###############################################################################
class FeatureVector:
    valueId = ""         # index of value in list of templates
    mentionId = ""        # index of mention in list of templates
    label = ""           # class label for fv
    qTemplate = None
    mTemplate = None
    features = []        # list of features
    prob = 0.0           # predicted probabilty from classifier
    noFeatures = False   # features vector is empty
    #  featureNumbers = {'VALUE_BEFORE':0, 'CLOSEST':1, 'BIN_PARITY':2,\
    #        'CONTAINS_SEP':3, 'GROUP_IB':4, 'OUTCOME_IB':5, 'GROUP_SIZE_IB':6, \
    #        'OUTCOME_NUMBER_IB':7, 'NO_FEATURES':8, 'DEPENDENCY_EXISTS':9}
    def __init__(self, valueId, mentionId, label):
        self.valueId = valueId
        self.mentionId = mentionId
        self.label = label
        #    self.features = zeros(len(self.featureNumbers))
        self.features = set([])
        self.prob = 0.0
        self.noFeatures = True
        self.qTemplate = None
        self.mTemplate = None

    def addList(self, featureList):
        """ add list of features to feature vector """
        #    print 'addList:', featureList == None, featureList, len(featureList)
        for f in featureList:
            self.add(f)

    # add a new binary feature to the feature vector
    def add(self, featureName):
        #    fn = self.featureNumbers[featureName]
        #    self.features[fn] = 1
        #    self.noFeatures = False
        self.features.add(featureName)

    # write feature vector to a file formated for megam
    # <label> <feature1> ... <featureN>
    def writeToMegamFile(self, out):
        out.write(self.label)
        #    for f in self.featureNumbers.keys():
        #      if self.features[self.featureNumbers[f]] == 1:
        if len(self.features) == 0:
            out.write(' NO_FEATURES')
        else:
            for f in self.features:
                out.write(' ' + f)
        out.write('\n')

        # write feature vectors to test/training file
    def write(self, out):
        out.write(self.label)
        if self.noFeatures == True:
            out.write('\t'+str(self.featureNumbers['NO_FEATURES']+1)+':1')
        else:
            for i in range(0, len(self.features)):
                if self.features[i] > 0:
                    out.write('\t'+str(i+1)+':1')
        out.write('\n')


#######################################################################
# class definition for object that associates two entity templates
#######################################################################

class BaseAssociator(Finder):
    """ base class for train/test system that associates mentions
        with quantities in a sentence """
    useLabels = True      # if True, use detected mentions and quantities
    # otherwise, use annotated mentions and quantities

    def __init__(self, entityType1, entityType2, useLabels=True):
        """ create a new mention-quantity associator given a specific mention type
            and quantity type. """
        Finder.__init__(self, [entityType1, entityType2])
        self.finderType = 'associator'
        self.useLabels = useLabels

    def train(self, absList, modelfilename):
        """ Train a mention-quantity associator model given a list of abstracts """
        raise NotImplementedError("Need to implement train()")

    def test(self, absList, modelfilename):
        """ Apply the mention-quantity associator to a given list of abstracts
            using the given model file.
            """
        raise NotImplementedError("Need to implement test()")

    def computeFeatures(self, absList, mode=''):
        """ compute classifier features for each mention-quantity pair in
            each sentence in each abstract in a given list of abstracts. """
        for abs in absList:
            for sentence in abs.sentences:
                #        if sentence.templates == None:
                #          sentence.templates = Templates(sentence, useLabels=self.useLabels)
                #        if sentence.annotatedTemplates == None:
                #          sentence.annotatedTemplates = Templates(sentence, useLabels=False)
                if mode == 'train':
                    self.computeTemplateFeatures(sentence.annotatedTemplates, mode)
                else:
                    self.computeTemplateFeatures(sentence.templates, mode)



    def computeTemplateFeatures(self, templates, mode=''):
        """ compute classifier features for each mention-quantity pair in
            a given sentence in an abstract. """
        raise NotImplementedError("Need to implement computeTemplateFeatures()")


    def computeStats(self, absList, statOut=None, errorOut=None, typeList=[], keyPrefix=''):
        """ compute RPF stats for associated mentions and quantities in a list
            of abstracts.

            write final RPF stats to statOut
            write TP/FP/FN to errorOut
        """
        if len(keyPrefix) == 0:
            keyPrefix = 'Assoc - '

        if len(typeList) > 0:
            statDescription = '-'.join(typeList)
        else:
            statDescription = self.entityTypesString

        stats = EntityStats([statDescription])

        totalFalsePairs = 0
        for abs in absList:
            errorOut.write('---%s (%s)\n'%(abs.id, statDescription))
            for s in abs.sentences:
                [tp, fp, fn, falsePairs] = self.checkAssociations(s, errorOut, typeList)
                errorOut.write('tp: %d, fp: %d, fn: %d, falsePairs: %d\n'%(tp, fp, fn, falsePairs))
                totalFalsePairs += falsePairs
                stats.irstats[statDescription].addTP(tp)
                stats.irstats[statDescription].addFP(fp)
                stats.irstats[statDescription].addFN(fn)
        stats.printStats()
        print 'Total false pairs: ', totalFalsePairs
        #    stats.writeStats(statOut)
        stats.saveStats(statOut, keyPrefix=keyPrefix)
        return stats

    def checkAssociations(self, sentence, errorOut, typeList=[]):
        """ return number of correct associations and total number of values for
             a given mention and value type """
        raise NotImplementedError("Need to implement checkAssociations()")


    def linkTemplates(self, sentence):
        """ link value template to best matching mention template in the same sentence"""
        raise NotImplementedError("Need to implement linkTemplates()")

#######################################################################
# class definition for object that associates mentions with quantities
#######################################################################

class BaseMentionQuantityAssociator(BaseAssociator):
    """ base class for train/test system that associates mentions
        with quantities in a sentence """
    mentionType = ''      # type of mention to associate with a quantity
    quantityType = ''     # type of quantity to associate with a mention

    validMentionTypes = set(['group', 'outcome', 'time'])
    validQuantityTypes = set(['on', 'eventrate', 'gs', 'cost_value'])

    def __init__(self, mentionType, quantityType, useLabels=True):
        """ create a new mention-quantity associator given a specific mention type
            and quantity type. """
        BaseAssociator.__init__(self, mentionType, quantityType, useLabels)
        self.finderType = 'mq-associator'
        self.mentionType = mentionType
        self.quantityType = quantityType

    def linkQuantityAndMention(self, qTemplate, mTemplate, prob):
        """ link a quantity and mention template """
        qTemplate.group = mTemplate
        qTemplate.groupProb = prob
        mTemplate.addSize(qTemplate)


    def checkAssociations(self, sentence, errorOut, typeList=[]):
        """ return number of correct associations and total number of values for
             a given mention and value type """
        if len(typeList) == 2:
            if typeList[0] in self.validMentionTypes and typeList[1] in self.validQuantityTypes:
                mentionType = typeList[0]
                quantityType = typeList[1]
            elif typeList[1] in self.validMentionTypes and typeList[0] in self.validQuantityTypes:
                mentionType = typeList[0]
                quantityType = typeList[1]
            else:
                raise StandardError('Illegal type list for checkAssociations: ' + typeList)
        elif len(typeList) == 0:
            mentionType = self.mentionType
            quantityType = self.quantityType
        else:
            raise StandardError('Illegal number of types for checkAssociations: %d'%len(typeList))

        tp = 0
        fp = 0
        fn = 0
        falsePairs = 0
        mTemplateList = sentence.templates.getList(mentionType)
        for qTemplate in sentence.templates.getList(quantityType):
            associationCorrect = qTemplate.correctAssociation(mentionType)
            if mentionType == 'group' and qTemplate.group != None:
                mentionName = qTemplate.group.name
            elif mentionType == 'outcome' and qTemplate.outcome != None:
                mentionName = qTemplate.outcome.name
            else:
                mentionName = None

            #      errorOut.write(qTemplate.toString()+', correct='+str(associationCorrect)+'\n')
            if associationCorrect == 1:
                # both value and mention are valid and are correctly associated
                tp += 1
                errorOut.write('+TP: %s=%f, %s\n' %(quantityType, qTemplate.value, mentionName))
            elif associationCorrect == 0:
                # either the value or mention is incorrect
                # or both are valid, but should not be associated
                # results in a false positive in all cases
                fp += 1
                if qTemplate.token.hasAnnotation(quantityType) == False:
                    falsePairs += 1
                errorOut.write('-FP: %s=%f, %s \n' %(quantityType, qTemplate.value, mentionName))

            # check for false negative
            if associationCorrect != 1 and qTemplate.isTruePositive():
                for mTemplate in mTemplateList:
                    if qTemplate.shouldBeAssociated(mTemplate):
                        # this is the mention that the quantity should have been matched with,
                        # but was not.
                        fn += 1
                        errorOut.write(' -FN: %s=%f be associated with %s\n' % (quantityType, qTemplate.value, mTemplate.name))
                        break

        return [tp, fp, fn, falsePairs]


#######################################################################
# class definition for an association between group/outcome and outcome measurements
#######################################################################

class OutcomeMeasurementAssociation:
    group = None
    outcome = None
    outcomeMeasurement = None
    prob = None

    def __init__(self, group, outcome, outcomeMeasurement, prob):
        self.group = group
        self.outcome = outcome
        self.outcomeMeasurement = outcomeMeasurement
        self.prob = prob

    def getValueString(self):
        omValueStrings = []
        er = self.outcomeMeasurement.getTextEventRate()
        on = self.outcomeMeasurement.getOutcomeNumber()

        if er != None:
            omValueStrings.append('ER=%.4f'%er.value)
        if on != None:
            omValueStrings.append('ON=%d'%on.value)
        omString = ','.join(omValueStrings)
        return omString

    def toString(self):
        omString = self.getValueString()

        if self.group == None:
            gName = 'None'
        else:
            gName = self.group.name

        if self.outcome == None:
            oName = 'None'
        else:
            oName = self.outcome.name

        return 'prob=%.4f, om=(%s), group=%s, outcome=%s'%(self.prob, omString, gName, oName)

class TrueOutcomeMeasurementAssociation:
    """ a true association of detected event rate, outcome number, group and outcome """
    eventrate = None
    outcomeNumber = None
    groupSet = None
    outcomeSet = None
    match = None

    def __init__(self, groupSet=set([]), outcomeSet=([]), eventrate=None, outcomeNumber=None):
        self.groupSet = groupSet
        self.outcomeSet = outcomeSet
        self.outcomeNumber = outcomeNumber
        self.eventrate = eventrate
        self.match = None

    def toString(self):
        """ write contents of association to a string """
        s = ''
        if self.eventrate != None:
            s += 'er=%.4f, '%self.eventrate.value
        else:
            s += 'er=None, '

        if self.outcomeNumber != None:
            s += 'on=%d, '%self.outcomeNumber.value
        else:
            s += 'on=None, '

        s += 'groups: '
        for group in self.groupSet:
            s += group.name + ' | '

        s += ', outcomes: '
        for outcome in self.outcomeSet:
            s += outcome.name + ' | '

        return s


    #######################################################################
# class definition for object that associates mentions with outcome measurements
#######################################################################

class BaseOutcomeMeasurementAssociator(BaseMentionQuantityAssociator):
    """ train/test system that associates eventrates and outcome numbers with groups and outcomes """

    pairTypeList = [['outcome', 'on'], ['outcome', 'eventrate'],
                    ['group', 'on'], ['group', 'eventrate']]
    statList = None
    associationList = None
    incompleteMatches = None

    def __init__(self, useLabels=True):
        """ create a new group size, group associator. """
        BaseMentionQuantityAssociator.__init__(self, 'group-outcome', 'on-eventrate', useLabels)

        self.statList = StatList()
        self.associationList = {}
        self.incompleteMatches = {}


    def train(self, absList, modelFilename):
        """ Train a mention-quantity associator model given a list of abstracts """
        raise NotImplementedError("Need to implement train()")

    def test(self, absList, modelFilename, fold=None):
        """ Apply the mention-quantity associator to a given list of abstracts
            using the given model file.
            """
        raise NotImplementedError("Need to implement test()")


    def getFeatureVectors(self, absList, forTraining):
        """ Ignored. """
        pass

    def computeTemplateFeatures(self, templates, mode=''):
        """ compute classifier features for each mention-quantity pair in
            a given sentence in an abstract. """
        pass

    def groupOutcomeOverlap(self, group, outcome):
        """ return True if there is unacceptable overlap between a group and outcome mention """
        nMatched = 0
        nUnmatched1 = 0
        nUnmatched2 = 0

        gWords = group.mention.allWords()
        oWords = outcome.mention.allWords()
        nMatched = len(gWords.intersection(oWords))
        if nMatched == len(gWords) and nMatched == len(oWords):
            return True
        else:
            return False

        #     groupLemmas = group.mention.interestingLemmas()
        #     outcomeLemmas = outcome.mention.interestingLemmas()
        #
        #     nMatched = len(groupLemmas.intersection(outcomeLemmas))
        #     #
        #     nGroupLemmas = len(groupLemmas)
        #     nOutcomeLemmas = len(outcomeLemmas)
        #     if nMatched > 0 and float(nMatched)/nGroupLemmas > 0.74 and float(nMatched)/nOutcomeLemmas > 0.74:
        #       return True
        #     else:
        #       return False

    def linkTemplates(self, sentence):
        """ link group size and group templates using Hungarian matching algorithm """
        raise NotImplementedError("Need to implement linkTemplates()")


    def linkOutcomeMeasurementAssociations(self, om, group, outcome, prob):
        """ link outcome measurement to group and outcome template """
        er = om.getTextEventRate()
        on = om.getOutcomeNumber()

        if er != None:
            outcomeFV = er.getMatchFeatures(outcome)
            groupFV = er.getMatchFeatures(group)
            if groupFV != None:
                er.groupProb = groupFV.prob
            if outcomeFV != None:
                er.outcomeProb = outcomeFV.prob

        if on != None:
            outcomeFV = on.getMatchFeatures(outcome)
            groupFV = on.getMatchFeatures(group)
            if groupFV != None:
                on.groupProb = groupFV.prob
            if outcomeFV != None:
                on.outcomeProb = outcomeFV.prob

        if groupFV != None:
            gTemplate = groupFV.mTemplate
        else:
            if er != None:
                gTemplate = er.group
            else:
                gTemplate = on.group

        if outcomeFV != None:
            oTemplate = outcomeFV.mTemplate
        else:
            if er != None:
                oTemplate = er.outcome
            else:
                oTemplate = on.outcome

        om.addGroup(gTemplate)
        om.addOutcome(oTemplate)
        abstract = group.getAbstract()
        if abstract not in self.associationList:
            self.associationList[abstract] = []
        self.associationList[abstract].append(OutcomeMeasurementAssociation(group, outcome, om, prob))


    def buildTrueAssociations(self, abstract):
        """ build list of true outcomeSet measurement associations for an abstract """
        trueAssociations = []
        for sentence in abstract.sentences:
            templates = sentence.templates
            onList = templates.getList('on')
            erList = templates.getList('eventrate')
            groupList = templates.getList('group')
            outcomeList = templates.getList('outcome')

            # match event rates and on with group and outcome mentions in the same sentence
            for er in erList:
                if er.isTruePositive():
                    # find groupSet and outcomeSet
                    groupSet = set([])
                    outcomeSet = set([])
                    for gTemplate in groupList:
                        if er.shouldBeAssociated(gTemplate):
                            #              groupSet.add(gTemplate)
                            groupSet.add(gTemplate.rootMention())

                    for oTemplate in outcomeList:
                        if er.shouldBeAssociated(oTemplate):
                            #              outcomeSet.add(oTemplate)
                            outcomeSet.add(oTemplate.rootMention())
                    if len(groupSet) > 0 and len(outcomeSet) > 0:
                        trueAssociations.append(TrueOutcomeMeasurementAssociation(eventrate=er, groupSet=groupSet, outcomeSet=outcomeSet))

            for on in onList:
                if on.isTruePositive():
                    # check if on should be added to an existing association
                    foundMatch = False
                    for ta in trueAssociations:
                        if ta.outcomeNumber == None and on.shouldBelongToSameOutcomeMeasurement(ta.eventrate):
                            foundMatch = True
                            ta.outcomeNumber = on
                            break

                    if foundMatch == False:
                        # not part of an existing OM, must be its own
                        groupSet = set([])
                        outcomeSet = set([])
                        for gTemplate in groupList:
                            if on.shouldBeAssociated(gTemplate):
                                #                groupSet.add(gTemplate)
                                groupSet.add(gTemplate.rootMention())

                        for oTemplate in outcomeList:
                            if on.shouldBeAssociated(oTemplate):
                                #                outcomeSet.add(oTemplate)
                                outcomeSet.add(oTemplate.rootMention())

                        canComputeER = False
                        if on.hasAssociatedGroupSize() and on.groupSizeIsCorrect():
                            canComputeER = True
                        else:
                            for gTemplate in groupSet:
                                gs = gTemplate.getClosestGroupSize(sentenceIndex=sentence.index)
                                if gs != None and gs.shouldBeAssociated(gTemplate):
                                    canComputeER = True
                                    break
                        if canComputeER and len(groupSet) > 0 and len(outcomeSet) > 0:
                            # only add to list of om, g, o associations if we can compute and event rate with it
                            trueAssociations.append(TrueOutcomeMeasurementAssociation(outcomeNumber=on, groupSet=groupSet, outcomeSet=outcomeSet))


        return trueAssociations


    def computeStats(self, absList, statOut=None, errorOut=None, typeList=[]):
        """ compute RPF stats for associated outcome measurements and group and outcome mentions in a list
            of abstracts.

            write final RPF stats to statOut
            write TP/FP/FN to errorOut
        """
        statOut.copy(self.statList)

        # how many of the associations are correct/incorrect?
        statDescription = '(G,O) - OM'
        stats = EntityStats([statDescription])
        taFile = open('trueassociations.%s.txt'%self.finderType, 'w')
        for abstract in absList:
            errorOut.write('---%s ---\n'%(abstract.id))
            trueAssociations = self.buildTrueAssociations(abstract)

            taFile.write('---%s ---\n'%(abstract.id))
            for ta in trueAssociations:
                taFile.write(ta.toString() + '\n')

            if abstract in self.associationList:
                for omAssociation in self.associationList[abstract]:
                    group = omAssociation.outcomeMeasurement.getGroup()
                    outcome = omAssociation.outcomeMeasurement.getOutcome()
                    er = omAssociation.outcomeMeasurement.getTextEventRate()
                    on = omAssociation.outcomeMeasurement.getOutcomeNumber()

                    errorMsgs = []
                    matchFound = False
                    for ta in trueAssociations:
                        if ta.match == None and ((er != None and er == ta.eventrate) or (on != None and on == ta.outcomeNumber)):
                            # we have a potential match. check to see if everything matches
                            errorMsgs = []
                            self.checkQuantity(er, group, outcome, errorMsgs)
                            self.checkQuantity(on, group, outcome, errorMsgs)
                            if len(errorMsgs) == 0:
                                matchFound = True
                                ta.match = omAssociation

                            break

                    if matchFound:
                        stats.irstats[statDescription].incTP()
                        prefix = '+TP'
                    else:
                        # we have a false positive
                        stats.irstats[statDescription].incFP()
                        prefix = '-FP'

                    errorOut.write('%s: %s\n'%(prefix, omAssociation.toString()))
                    if len(errorMsgs) > 0:
                        errorOut.write(', '.join(errorMsgs)+'\n')

            # look at those OMs that were not associated
            if abstract in self.incompleteMatches:
                self.__processIncompleteMatches(abstract, errorOut)

            # count false negatives
            for ta in trueAssociations:
                if ta.match == None:
                    stats.irstats[statDescription].incFN()
                    errorOut.write('-FN: %s\n'%(ta.toString()))

        taFile.close()
        stats.saveStats(statOut, keyPrefix='Assoc ')

    def computeStatsOld(self, absList, statOut=None, errorOut=None, typeList=[]):
        """ compute RPF stats for associated mentions and quantities in a list
            of abstracts.

            write final RPF stats to statOut
            write TP/FP/FN to errorOut
        """
        statOut.copy(self.statList)

        # how many of the associations are correct/incorrect?
        componentIncorrect = 0
        statDescription = '(G,O) - OM'
        stats = EntityStats([statDescription])
        for abstract in self.associationList.keys():
            errorOut.write('---%s ---\n'%(abstract.id))

            for omAssociation in self.associationList[abstract]:
                group = omAssociation.group
                outcome = omAssociation.outcome

                er = omAssociation.outcomeMeasurement.getTextEventRate()
                on = omAssociation.outcomeMeasurement.getOutcomeNumber()
                errorMsgs = []
                self.checkQuantity(er, group, outcome, errorMsgs)
                self.checkQuantity(on, group, outcome, errorMsgs)
                if len(errorMsgs) == 0:
                    stats.irstats[statDescription].incTP()
                    prefix = '+TP'
                else:
                    stats.irstats[statDescription].incFP()
                    prefix = '-FP'
                    if (er == None or er.isTruePositive()) and (on == None or on.isTruePositive()) \
                            and (er == None or on == None or on.shouldBelongToSameOutcomeMeasurement(er)):
                        # this outcome measurement is correct and should be associated
                        # this was a false negative and a false positive
                        stats.irstats[statDescription].incFN()
                        errorOut.write('-FN: %s\n'%(omAssociation.getValueString()))

                errorOut.write('%s: %s\n'%(prefix, omAssociation.toString()))
                if len(errorMsgs) > 0:
                    errorOut.write(', '.join(errorMsgs)+'\n')

            # look at those OMs that were not associated
            if abstract in self.incompleteMatches:
                self.__processIncompleteMatches(abstract, errorOut, stats, statDescription)

        for abstract in absList:
            if abstract not in self.associationList.keys():
                errorOut.write('---%s ---\n'%(abstract.id))
                if abstract in self.incompleteMatches:
                    self.__processIncompleteMatches(abstract, errorOut, stats, statDescription)

        stats.saveStats(statOut, keyPrefix='Assoc ')

    def __processIncompleteMatches(self, abstract, errorOut, stats=None, statDescription=None):
        for omAssociation in self.incompleteMatches[abstract]:
            er = omAssociation.outcomeMeasurement.getTextEventRate()
            on = omAssociation.outcomeMeasurement.getOutcomeNumber()
            errorMsgs = []
            associationMissed = False
            if (er == None or er.isTruePositive()) and (on == None or on.isTruePositive()) \
                    and (er == None or on == None or on.shouldBelongToSameOutcomeMeasurement(er)):
                # this outcome measurement is correct and should be associated
                # this was a false negative
                if stats != None and statDescription != None:
                    stats.irstats[statDescription].incFN()
                errorOut.write('-IncompleteMatch: %s\n'%(omAssociation.getValueString()))

                # check for false negative, i.e. the G,O should be associated with this OM
                group = omAssociation.group
                outcome = omAssociation.outcome
                if group != None and outcome != None:
                    if er != None:
                        self.checkQuantity(er, group, outcome, errorMsgs)
                    if on != None:
                        self.checkQuantity(on, group, outcome, errorMsgs)
                    if len(errorMsgs) == 0:
                        # both the group and outcome should have been associated with this outcome measurement
                        # but they were not, this is a false negative
                        associationMissed = True
                        errorOut.write('   -PROB TOO LOW: %s\n'%(omAssociation.toString()))

            if associationMissed == False:
                errorOut.write('   + (correctly missed): %s\n'%(omAssociation.toString()))
                if len(errorMsgs) > 0:
                    errorOut.write(', '.join(errorMsgs)+'\n')

    def checkQuantity(self, qTemplate, group, outcome, errorMsgs):
        """ check if the group, outcome associations for a given quantity are correct.
            If not add error messages to given list of error message strings """
        if qTemplate != None:
            if qTemplate.shouldBeAssociated(group) == False:
                errorMsgs.append('WRONG GROUP')
            if qTemplate.shouldBeAssociated(outcome) == False:
                errorMsgs.append('WRONG OUTCOME')
      
  