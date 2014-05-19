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
        templates = sentence.templates
        costValueList = templates.getList('cost_value')
        outcomeList = templates.getList('outcome')
        groupList = templates.getList('group')

        nCostValues = len(costValueList)
        nGroupOutcomePairs = len(outcomeList)*len(groupList)

        if nGroupOutcomePairs == 0 or nCostValues == 0:
            return

        maxSize = max(nCostValues, nGroupOutcomePairs)

        # build list of group-outcome pairs
        goPairs = []
        for group in groupList:
            for outcome in outcomeList:
                goPairs.append((group, outcome))

        # initialize cost matrix for matching cost values with group,outcome pairs
        probMatrix = []
        probMultiplier = 100000

        for cvIdx in range(maxSize):
            probMatrix.append([])
            for goIdx in range(maxSize):
                if cvIdx < nCostValues and goIdx < nGroupOutcomePairs:
                    cv = costValueList[cvIdx]
                    (group, outcome) = goPairs[goIdx]

                    outcomeFV = cv.getMatchFeatures(outcome)
                    groupFV = cv.getMatchFeatures(group)
                    groupProb = groupFV.prob
                    outcomeProb = outcomeFV.prob
                    prob = round(groupProb * outcomeProb * probMultiplier)
                else:
                    # no association can be made
                    # this possible match involves either a dummy cost value or a dummy (group,outcome) pair
                    prob = 0

                probMatrix[cvIdx].append(prob)

        costMatrix = munkres.make_cost_matrix(probMatrix, lambda cost: probMultiplier - cost)
        m = munkres.Munkres()
        #    print probMatrix
        #    print costMatrix
        indices = m.compute(costMatrix)
        # threshold is (1/2)^4
        # threshold = 0.0625 * probMultiplier
        threshold = 0.0001 * probMultiplier
        #    threshold = 0.25 * probMultiplier

        for cvIdx, goIdx in indices:
            if cvIdx < nCostValues and goIdx < nGroupOutcomePairs:
                prob = probMatrix[cvIdx][goIdx]
                if prob > threshold:
                    # this quantity and mention should be associated
                    prob = float(prob) / probMultiplier
                    om = costValueList[cvIdx]
                    (group, outcome) = goPairs[goIdx]
                    self.linkOutcomeMeasurementAssociations(om, group, outcome, prob)

            # # record those outcome measurements that were not successfully matched to G,O
            # if cvIdx < nCostValues and (goIdx >= nGroupOutcomePairs or probMatrix[cvIdx][goIdx] <= threshold):
            #     om = costValueList[cvIdx]
            #     prob = float(probMatrix[cvIdx][goIdx])/probMultiplier
            #     if goIdx < nGroupOutcomePairs:
            #         (group, outcome) = goPairs[goIdx]
            #     else:
            #         group = None
            #         outcome = None
            #     abstract = sentence.abstract
            #     if abstract not in self.incompleteMatches:
            #         self.incompleteMatches[abstract] = []
            #     self.incompleteMatches[abstract].append(baseassociator.OutcomeMeasurementAssociation(group,
            #                                                                                          outcome, om, prob))


    def linkOutcomeMeasurementAssociations(self, cv, group, outcome, prob):
        """ link outcome measurement (a cost value in this case) to group and outcome template """
        if cv is None or group is None or outcome is None:
            return

        # add links from cost value to (group,outcome) pair
        cv.addGroup(group)
        cv.addOutcome(outcome)
        group.addCostValue(cv)
        outcome.addCostValue(cv)


#######################################################################
# class definition for object that associates mentions with eventrates and outcome numbers
#######################################################################

class OutcomeCostValuePairProbabilityEstimator(outcomemeasurementassociator.OutcomeMeasurementPairProbabilityEstimator):
    """ train/test system that associates eventrates and outcome numbers with groups and outcomes """

    def __init__(self, mentionType, quantityType, useLabels=True):
        """ create a new group size, group associator. """
        outcomemeasurementassociator.OutcomeMeasurementPairProbabilityEstimator.__init__(self, mentionType,
                                                                                         quantityType,
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