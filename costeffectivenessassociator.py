#!/usr/bin/env python 

"""
Associate Cost effectiveness terms with their values
"""

__author__ = 'Rodney L. Summerscales'


import mentionquantityassociator
import outcomemeasurementassociator
import math
import munkres
import baseassociator
import findertask

class CostEffectivenessAssociator(baseassociator.BaseOutcomeMeasurementAssociator):
    """ train/test system that associates cost terms with cost values in a sentence """

    __algorithm = ''
    probabilityEstimatorTasks = []
    pairTypeList = [['outcome', 'cost_value'], ['group', 'cost_value']]

    def __init__(self, modelPath, algorithm, useLabels=True):
        """ create a new group size, group associator.
            algorithm = 'hungarian' to use Hungarian matching algorithm with classifier determined pair prob
                        'greedy'   to match value with closest term.
        """
        if algorithm in {'hungarian', 'greedy'}:
            self.__algorithm = algorithm
        else:
            raise ValueError(algorithm+" is not a valid association algorithm")

        baseassociator.BaseOutcomeMeasurementAssociator.__init__(self, useLabels)
        self.finderType = 'cv-associator'

        probEstimators = []
        for [mType, qType] in self.pairTypeList:
            finder = OutcomeCostValuePairProbabilityEstimator(mType, qType)
            probEstimators.append(finder)

        self.probabilityEstimatorTasks = []
        for finder in probEstimators:
            finderTask = findertask.FinderTask(finder, modelPath=modelPath)
            self.probabilityEstimatorTasks.append(finderTask)

    def linkTemplates(self, sentence):
        """ Link a cost effectiveness term with a value
        """
        if self.__algorithm == 'hungarian':
            self.linkTemplatesHungarian(sentence)
        else:
            self.linkTemplatesGreedy(sentence)

    def train(self, absList, modelFilename):
        """ Train a mention-quantity associator model given a list of abstracts """
        pass

    def test(self, absList, modelFilename, fold=None):
        """ Apply the mention-quantity associator to a given list of abstracts
            using the given model file.
            """
        self.statList.clear()
        for probEstTask in self.probabilityEstimatorTasks:
            probEstTask.test(absList, statOut=self.statList, fold=fold)

        # chose the most likely association for each value
        self.associationList = {}         # list of (G,O, OM) associations made
        self.incompleteMatches = {}
        for abstract in absList:
            for s in abstract.sentences:
                self.linkTemplates(s)

    def linkTemplatesGreedy(self, sentence):
        """ Link cost values with closest group and outcome templates in the sentence
            (TODO: implement linkTemplatesGreedy())
        """
        pass

    def linkTemplatesHungarian(self, sentence):
        """ link group size and group templates using Hungarian matching algorithm """
        #    print 'linking all templates'
        pass

        # templates = sentence.templates
        # onList = templates.getList('on')
        # erList = templates.getList('eventrate')
        # outcomeMeasurements = templates.getOutcomeMeasurementList()
        # groupList = sentence.abstract.entities.lists['group']
        # outcomeList = sentence.abstract.entities.lists['outcome']
        #
        # nON = len(onList)
        # nER = len(erList)
        # nGroups = len(groupList)
        # nOutcomes = len(outcomeList)
        # nGroupOutcomePairs = nGroups * nOutcomes
        # if (nON + nER) == 0 or nGroupOutcomePairs == 0:
        #     return  # missing key information cannot make any associations
        #
        # goPairs = []
        # for group in groupList:
        #     for outcome in outcomeList:
        #         #        goPairs.append((group,outcome))
        #
        #         (nMatched, nUnmatched1, nUnmatched2) = group.partialSetMatch(outcome)
        #
        #         if not self.groupOutcomeOverlap(group, outcome):
        #             # overlap between group/outcome may be no more than ONE word and this may be no more than 1/3 of smaller mention
        #             goPairs.append((group,outcome))
        #         else:
        #             print sentence.abstract.id, '#### skipping:', group.rootMention().name, ';', outcome.rootMention().name
        #
        # nGroupOutcomePairs = len(goPairs)
        # if nGroupOutcomePairs == 0:
        #     return  # missing key information cannot make any associations
        #
        #
        # # get unmatched event rates and outcome numbers
        # unmatchedON = []
        # unmatchedER = []
        # for om in outcomeMeasurements:
        #     on = om.getOutcomeNumber()
        #     er = om.getTextEventRate()
        #     if er is not None and on is None:
        #         # unmatched event rate
        #         unmatchedER.append(er)
        #     elif on is not None and er is None:
        #         # unmatched number of outcomes
        #         unmatchedON.append(on)
        #
        # # identify as of yet unmatched event rates and outcome numbers that could potentially match each other
        # erMatches = {}
        # onMatches = {}
        # for on in unmatchedON:
        #     onMatches[on] = []
        # for er in unmatchedER:
        #     erMatches[er] = []
        #
        # for on in unmatchedON:
        #     couldCalculateER = False
        #     if on.hasAssociatedGroupSize():
        #         calculatedER = on.eventRate()
        #         couldCalculateER = True
        #         for er in unmatchedER:
        #             if er.equivalentEventRates(calculatedER):
        #                 onMatches[on].append(er)
        #                 erMatches[er].append(on)
        #     else:
        #         for group in groupList:
        #             groupFV = on.getMatchFeatures(group)
        #             if groupFV is not None and groupFV.prob > 0:
        #                 # it is possible to associate with this group
        #                 gs = group.getSize(sentenceIndex=sentence.index)
        #                 if gs > 0:
        #                     calculatedER = on.eventRate(groupSize=gs)
        #                     couldCalculateER = True
        #                     for er in unmatchedER:
        #                         if er.equivalentEventRates(calculatedER):
        #                             onMatches[on].append(er)
        #                             erMatches[er].append(on)
        #     if not couldCalculateER:
        #         outcomeMeasurements.remove(on.outcomeMeasurement)
        #
        # # discard any outcome numbers that potentially match multiple event rates
        # for on in onMatches.keys():
        #     if len(onMatches[on]) == 1 and len(erMatches[onMatches[on][0]]) == 1:
        #         # this outcome number is a potential match for only one event rate
        #         # similarly, the event rate is only a match for this outcome number
        #         # assume they belong to same outcome measurement
        #         erOM = er.outcomeMeasurement
        #         on.outcomeMeasurement.addEventRate(er)
        #         outcomeMeasurements.remove(erOM)
        #
        #         # now consider all possible valid ON,ER pairings
        #     #    for on in unmatchedON:
        #     #      for er in unmatchedER:
        #     #        if on.hasAssociatedGroupSize() == False or on.equivalentEventRates(er.eventRate()) == True:
        #     #          om = OutcomeMeasurement(on)
        #     #          om.addEventRate(er)
        #     #          outcomeMeasurements.append(om)
        #
        # nOutcomeMeasurements = len(outcomeMeasurements)
        # maxSize = max(nOutcomeMeasurements, nGroupOutcomePairs)
        #
        # # initialize cost matrix for matching outcome measurements with group,outcome pairs
        # probMatrix = []
        # probMultiplier = 100000
        #
        # for omIdx in range(maxSize):
        #     probMatrix.append([])
        #     for goIdx in range(maxSize):
        #         if omIdx < nOutcomeMeasurements and goIdx < nGroupOutcomePairs:
        #             om = outcomeMeasurements[omIdx]
        #             (group, outcome) = goPairs[goIdx]
        #             er = om.getTextEventRate()
        #             on = om.getOutcomeNumber()
        #
        #             if er is not None:
        #                 outcomeFV = er.getMatchFeatures(outcome)
        #                 groupFV = er.getMatchFeatures(group)
        #                 if outcomeFV is None or groupFV is None:
        #                     # this quantity has no chance of being associated with either the group or outcome mention
        #                     # this can happen if all mentions for the entity appear in a sentence after the quantity
        #                     probG_ER = 0
        #                     probO_ER = 0
        #                 else:
        #                     probO_ER = outcomeFV.prob
        #                     probG_ER = groupFV.prob
        #             else:
        #                 probG_ER = 1
        #                 probO_ER = 1
        #
        #             if on is not None:
        #                 # this outcome measurement has an outcome number
        #                 # is this number useful? Can we compute an event rate for this group?
        #                 # If not, discard this measurement (set probability to zero).
        #                 # if so, is the event rate compatible with the textual event rate?
        #                 # If not, discard.
        #                 calculatedER = -1
        #                 gs = group.getSize(sentenceIndex=sentence.index)
        #                 outcomeFV = on.getMatchFeatures(outcome)
        #                 groupFV = on.getMatchFeatures(group)
        #                 if outcomeFV is None or groupFV is None:
        #                     # this quantity has no chance of being associated with either the group or outcome mention
        #                     probG_ON = 0
        #                     probO_ON = 0
        #                 else:
        #                     probO_ON = outcomeFV.prob
        #                     probG_ON = groupFV.prob
        #
        #                 if not on.hasAssociatedGroupSize():
        #                     # there is no group size already associated with the outcome number
        #                     # does the group have a group size?
        #                     # If so, is the resulting event rate compatible with the text one?
        #                     if gs <= 0 and er is None:
        #                         # there is no way to compute an event rate with this outcome measurement.
        #                         # it does not add any useful information.
        #                         # discard it by setting probability to zero
        #                         probG_ON = 0
        #                         probO_ON = 0
        #                     elif gs > 0:
        #                         # the proposed group has an associated size
        #                         # we can compute an event rate for this group/outcome
        #                         calculatedER = on.eventRate(groupSize=gs)
        #                         if (er is not None and er.equivalentEventRates(calculatedER) == False) or abs(calculatedER) > 1:
        #                             # event rates are incompatible
        #                             probG_ON = 0
        #                             probO_ON = 0
        #             else:
        #                 probG_ON = 1
        #                 probO_ON = 1
        #
        #             if er is not None and on is not None:
        #                 probG_OM = math.sqrt(probG_ER * probG_ON)
        #                 probO_OM = math.sqrt(probO_ER * probO_ON)
        #             elif er is not None:
        #                 probG_OM = probG_ER
        #                 probO_OM = probO_ER
        #             else:
        #                 # on != None
        #                 probG_OM = probG_ON
        #                 probO_OM = probO_ON
        #
        #             prob = round(probG_OM * probO_OM * probMultiplier)
        #         else:
        #             prob = 0
        #
        #         probMatrix[omIdx].append(prob)
        #
        #     #    if sentence.abstract.id == '21600592':
        #     #      for omIdx in range(maxSize):
        #     #        for goIdx in range(maxSize):
        #     #          if omIdx < nOutcomeMeasurements and goIdx < nGroupOutcomePairs:
        #     #            om = outcomeMeasurements[omIdx]
        #     #            (group, outcome) = goPairs[goIdx]
        #     #            print probMatrix[omIdx][goIdx], om.statisticString(), group.name, outcome.name
        #
        # costMatrix = munkres.make_cost_matrix(probMatrix, lambda cost: probMultiplier - cost)
        # m = munkres.Munkres()
        # #    print probMatrix
        # #    print costMatrix
        # indices = m.compute(costMatrix)
        # # threshold is (1/2)^4
        # threshold = 0.0625 * probMultiplier
        # threshold = 0.0001 * probMultiplier
        # #    threshold = 0.25 * probMultiplier
        #
        # for omIdx, goIdx in indices:
        #     if omIdx < nOutcomeMeasurements and goIdx < nGroupOutcomePairs:
        #         prob = probMatrix[omIdx][goIdx]
        #         if prob > threshold:
        #             # this quantity and mention should be associated
        #             prob = float(prob) / probMultiplier
        #             om = outcomeMeasurements[omIdx]
        #             (group, outcome) = goPairs[goIdx]
        #             self.linkOutcomeMeasurementAssociations(om, group, outcome, prob)
        #     # record those outcome measurements that were not succefully matched to G,O
        #     if omIdx < nOutcomeMeasurements and (goIdx >= nGroupOutcomePairs or probMatrix[omIdx][goIdx] <= threshold):
        #         om = outcomeMeasurements[omIdx]
        #         prob = float(probMatrix[omIdx][goIdx])/probMultiplier
        #         if goIdx < nGroupOutcomePairs:
        #             (group, outcome) = goPairs[goIdx]
        #         else:
        #             group = None
        #             outcome = None
        #         abstract = sentence.abstract
        #         if abstract not in self.incompleteMatches:
        #             self.incompleteMatches[abstract] = []
        #         self.incompleteMatches[abstract].append(baseassociator.OutcomeMeasurementAssociation(group, outcome, om, prob))





#######################################################################
# class definition for object that associates mentions with eventrates and outcome numbers
#######################################################################

class OutcomeCostValuePairProbabilityEstimator(outcomemeasurementassociator.OutcomeMeasurementPairProbabilityEstimator):
    """ train/test system that associates eventrates and outcome numbers with groups and outcomes """

    def __init__(self, mentionType, quantityType, useLabels=True):
        """ create a new group size, group associator. """
        outcomemeasurementassociator.OutcomeMeasurementPairProbabilityEstimator.__init__(self, mentionType, quantityType,
                                                                                         useLabels,
                                                                                         considerPreviousSentences=False)
    def getDefaultModelFilename(self):
        """ Return the default filename used for creating a model file during train
        """
        modelFilename = self.entityTypesToString([self.mentionType, 'eventrate'])
        return modelFilename


    def train(self, absList, modelFilename):
        """ Train a mention-quantity associator model given a list of abstracts.
            For now use models learned from group/outcome - outcome number/event rate association
         """
        pass

